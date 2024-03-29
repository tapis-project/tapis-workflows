import time, logging

from kubernetes import client, watch # TODO watch.Watch?

from conf.constants import (
    KUBERNETES_NAMESPACE,
    WORKFLOW_NFS_SERVER,
    KANIKO_IMAGE_URL,
    KANIKO_IMAGE_TAG
)
from core.tasks.BaseBuildExecutor import BaseBuildExecutor
from core.resources import ConfigMapResource, JobResource
from utils import get_flavor, lbuffer_str as lbuf
from utils.k8s import flavor_to_k8s_resource_reqs, gen_resource_name
from errors import WorkflowTerminated


PSTR = lbuf('[PIPELINE]')
TSTR = lbuf('[TASK]')

class Kaniko(BaseBuildExecutor):
    def __init__(self, task, ctx, exchange, plugins=[]):
        BaseBuildExecutor.__init__(self, task, ctx, exchange, plugins=plugins)

        self._configmap = None
        self._container_docker_cache_dir = "/cache"

    def execute(self):
        # Create the kaniko job. Return a failed task result on exception
        # with the error message as the str value of the exception
        try: 
            job = self._create_job()
            # Poll the job status until the job is in a terminal state
            while not self._job_in_terminal_state(job):
                if self.terminating:
                    raise WorkflowTerminated()
                job = self.batch_v1_api.read_namespaced_job(
                    job.metadata.name, KUBERNETES_NAMESPACE
                )

                time.sleep(self.polling_interval)
        except WorkflowTerminated as e:
            # Log the Termination Error
            self.ctx.logger.error(str(e))
            self.cleanup(terminating=True)
            return self._task_result(2, errors=[e])
        except Exception as e:
            self.ctx.logger.error(str(e))
            return self._task_result(1, errors=[e])

        # Get the job's pod name
        pod_list = self.core_v1_api.list_namespaced_pod(
            namespace=KUBERNETES_NAMESPACE,
            label_selector=f"job-name={job.metadata.name}"
        )

        pod_name = pod_list.items[0].metadata.name

        # Get the logs(stdout) from this job's pod
        logs = None
        try:
            # for line in watch.stream(
            #     self.core_v1_api.read_namespaced_pod_log,
            #     name=pod_name,
            #     namespace=KUBERNETES_NAMESPACE
            # ):
            #    self._stdout(line, flag="ab")

            logs = self.core_v1_api.read_namespaced_pod_log(
                name=pod_name,
                namespace=KUBERNETES_NAMESPACE,
                _return_http_data_only=True,
                _preload_content=False,
            ).data  # .decode("utf-8")
            self._stdout(logs, flag="ab")

        except client.rest.ApiException as e:
            self.ctx.logger.error(f"Exception reading pod log: {e}")
            return self._task_result(1, errors=[e])
        except Exception as e:
            self.ctx.logger.error(str(e))
            return self._task_result(1, errors=[e])

        # TODO Validate the jobs outputs against outputs in the task definition

        return self._task_result(0 if self._job_succeeded(job) else 1)

    def _create_job(self):
        """Create a job in the Kubernetes cluster"""
        # Set the name for the k8 job metadata
        job_name = gen_resource_name(prefix="kib")

        # Create a list of the container args based on task properties.
        # A by-product of this process is the creation of the dockerhub configmap
        # that is mounted into the kaniko job container
        container_args = self._resolve_container_args(job_name)

        # List of volume mount objects for the container
        volume_mounts = []
        if self._configmap != None:
            volume_mounts = [
                # Volume mount for the registry credentials config map
                client.V1VolumeMount(
                    name="regcred",
                    mount_path="/kaniko/.docker/config.json",
                    sub_path="config.json",
                ),
                # Volume mount the task-workdir
                client.V1VolumeMount(
                    name="task-workdir",
                    mount_path=self.task.container_work_dir,
                ),
                # Volume mount the task-workdir
                client.V1VolumeMount(
                    name="kaniko-cache",
                    mount_path=self._container_docker_cache_dir,
                )
            ]

        # Container object
        container = client.V1Container(
            name="kaniko",
            image=f"{KANIKO_IMAGE_URL}:{KANIKO_IMAGE_TAG}",
            args=container_args,
            volume_mounts=volume_mounts,
            resources=flavor_to_k8s_resource_reqs(get_flavor("c1lrg"))
        )

        # List of volume objects
        volumes = []
        if self._configmap != None:
            volumes.append(
                # Volume for mounting the registry credentials
                client.V1Volume(
                    name="regcred",
                    config_map=client.V1ConfigMapVolumeSource(
                        name=self._configmap.metadata.name
                    ),
                )
            )
            
        # Volumes for configs
        volumes.append(
            client.V1Volume(
                name="task-workdir",
                nfs=client.V1NFSVolumeSource(
                    server=WORKFLOW_NFS_SERVER,
                    path=self.task.nfs_work_dir
                ),
            )
        )
        
        # Volumes for caching
        volumes.append(
            client.V1Volume(
                name="kaniko-cache",
                nfs=client.V1NFSVolumeSource(
                    server=WORKFLOW_NFS_SERVER,
                    path=self.pipeline.nfs_docker_cache_dir
                ),
            )
        )

        # Pod template and pod template spec
        template = client.V1PodTemplateSpec(
            spec=client.V1PodSpec(
                containers=[container], restart_policy="Never", volumes=volumes
            )
        )

        # Job spec
        self.task.max_retries = 0 if self.task.max_retries < 0 else self.task.max_retries
        job_spec = client.V1JobSpec(
            backoff_limit=(self.task.max_retries), template=template)

        # Job metadata
        metadata = client.V1ObjectMeta(
            labels=dict(job=job_name),
            name=job_name,
            namespace=KUBERNETES_NAMESPACE,
        )

        # Job body
        body = client.V1Job(metadata=metadata, spec=job_spec)
        
        try:
            job = self.batch_v1_api.create_namespaced_job(
                namespace=KUBERNETES_NAMESPACE, body=body
            )
        except Exception as e:
            logging.critical(e)
            raise e

        # Register the job to be deleted after execution
        self._register_resource(JobResource(job=job))

        return job

    def _resolve_container_args(self, job_name):
        """Add the context, docerkfile, and destination(or --no-push) arguments that
        kaniko requires and create the dockerhub config file that will be mounted into the kaniko job container
        to authenticate with dockerhub"""

        container_args = []

        # Enable image layer caching for imporved performance
        container_args.append(f"--cache")
        container_args.append("--cache-run-layers=true")
        container_args.append("--cache-copy-layers=true")
        container_args.append(f"--cache-dir={self._container_docker_cache_dir}")

        # Source of dockerfile for image to be build
        context = self._resolve_context_string()
        container_args.append(f"--context={context}")

        # Useful when your context is, for example, a git repository,
        # and you want to build one of its subfolders instead of the root folder
        if self.task.context.sub_path != None:
            container_args.append(f"--context-sub-path={self.task.context.sub_path}")

        # The branch to be pulled
        container_args.append(f'--git="branch={self.task.context.branch}"')

        # Path to the Dockerfile in the repository. All paths prefixed with "/" will
        # have the forward slash removed
        container_args.append(f"--dockerfile={self.task.context.build_file_path.lstrip('/')}")

        # the image registry that the image will be pushed to
        destination = self._resolve_destination_string()

        destination_arg = f"--destination={destination}"
        if destination == None:
            destination_arg = "--no-push"

        container_args.append(destination_arg)

        # Create the dockerhub config map that will be mounted into the kaniko job container
        if destination != None:
            self._configmap = self._create_dockerhub_configmap(job_name)

        return container_args

    def _create_dockerhub_configmap(self, job_name):
        self._create_dockerhub_config()

        configmap_name = gen_resource_name(prefix="cm")

        # Setup ConfigMap metadata
        metadata = client.V1ObjectMeta(
            labels=dict(job=job_name),
            name=configmap_name,
            namespace=KUBERNETES_NAMESPACE,
        )

        # Get the contents of the dockerhub config file
        data = None
        with open(f"{self.dockerhub_config_dir}config.json", "r") as file:
            data = file.read()

        # Instantiate the configmap object
        body = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            data={"config.json": data},
            metadata=metadata,
        )

        configmap = self.core_v1_api.create_namespaced_config_map(
            namespace=KUBERNETES_NAMESPACE, body=body
        )

        # Because the configmap is mounted to the job, when the job is deleted during resource
        # cleanup, the config gets deleted as well
        self._register_resource(ConfigMapResource(configmap=configmap))

        return configmap
