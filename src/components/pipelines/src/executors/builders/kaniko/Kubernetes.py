import yaml

from kubernetes import client

from conf.configs import KUBERNETES_NAMESPACE
from core.ActionResult import ActionResult
from core.BaseBuildExecutor import BaseBuildExecutor
from core.resources import ConfigMapResource, JobResource


class Kubernetes(BaseBuildExecutor):
    def __init__(self, action, message):
        BaseBuildExecutor.__init__(self, action, message)

        self.configmap = None

    def execute(self, on_finish_callback) -> ActionResult:
        # Create the kaniko job
        job_name = self._create_kaniko_job()

        try:
            pod_log_response = self.core_v1_api.read_namespaced_pod_log(
                name=job_name,
                namespace=KUBERNETES_NAMESPACE,
                _return_http_data_only=True,
                _preload_content=False
            )
            pod_log = pod_log_response.data.decode("utf-8")
            print(pod_log)
        except Exception as e:
            print("Pipelines Error: ", e)

        # TODO implement on_finish_callback

        return ActionResult(status=0)

    def _create_kaniko_job(self):
        """Create a job in the Kubernetes cluster"""
        # Set the name for the k8 job metadata
        job_name = f"{self.group.id}.{self.pipeline.id}.{self.action.id}"

        # Create a list of the container args based on action properties.
        # A by-product of this process is the creation of the dockerhub configmap
        # that is mounted into the kaniko job container
        container_args = self._resolve_container_args(job_name)

        # List of volume mount objects for the container
        volume_mounts = []
        if self.configmap is not None:
            volume_mounts = [
                client.V1VolumeMount(
                    name="regcred",
                    mount_path="/kaniko/.docker/config.json",
                    sub_path="config.json"
                )
            ]

        # Container object
        container = client.V1Container(
            name="kaniko",
            image="gcr.io/kaniko-project/executor:debug",
            args=container_args,
            volume_mounts=volume_mounts
        )

        # List of volume objects
        volumes = []
        if self.configmap is not None:
            volumes=[
                client.V1Volume(
                    name="regcred",
                    config_map=client.V1ConfigMapVolumeSource(
                        name=self.configmap.metadata.name
                    )
                )
            ]

        # Pod template and pod template spec
        template = client.V1PodTemplateSpec(
            spec=client.V1PodSpec(
                containers=[container],
                restart_policy="Never",
                volumes=volumes
            )
        )

        # Job spec
        job_spec = client.V1JobSpec(
            backoff_limit=(self.action.retries + 1),
            template=template
        )

        # Job metadata
        metadata = client.V1ObjectMeta(
            labels=dict(job=job_name),
            name=job_name,
            namespace=KUBERNETES_NAMESPACE,
        )

        # Job body
        job = client.V1Job(
            metadata=metadata,
            spec=job_spec
        )

        self.batch_v1_api.create_namespaced_job(
            namespace=KUBERNETES_NAMESPACE,
            body=job
        )

        # Register the job to be deleted after execution
        self._register_resource(JobResource(job=job))

        return job_name

    def _resolve_container_args(self, job_name):
        """Add the context, docerkfile, and destination(or --no-push) arguments that
        kaniko requires and create the dockerhub config file that will be mounted into the kaniko job container
        to authenticate with dockerhub"""

        container_args = []

        # Enable image layer caching for imporved performance
        can_cache = self.action.cache or hasattr(self.directives, "CACHE")
        container_args.append(f"--cache={'true' if can_cache else 'false'}")

        # Source of dockerfile for image to be build
        context = self._resolve_context_string()
        container_args.append(f"--context={context}")

        # Useful when your context is, for example, a git repository,
        #  and you want to build one of its subfolders instead of the root folder
        if self.action.context.sub_path is not None:
            container_args.append(f"--context-sub-path={self.action.context.sub_path}")

        # The branch to be pulled
        container_args.append(f"--git=\"branch={self.action.context.branch}\"")

        # path to the Dockerfile in the repository
        container_args.append(f"--dockerfile={self.action.context.dockerfile_path}")

        # the image registry that the image will be pushed to
        destination = self._resolve_destination_string()
        destination_arg = "--no-push"

        if destination is not None:
            destination_arg = f"--destination={destination}"

        container_args.append(destination_arg)

        # Create the dockerhub config map that will be mounted into the kaniko job container
        if destination is not None:
            self.configmap = self._create_dockerhub_configmap(job_name)

        return container_args

    def _create_dockerhub_configmap(self, job_name):
        self._create_dockerhub_config()

        configmap_name = f"dockerhub.regcred.{job_name}"

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
        configmap = client.V1ConfigMap( 
            api_version="v1",
            kind="ConfigMap",
            data={"config.json": data},
            metadata=metadata
        )

        self.core_v1_api.create_namespaced_config_map(
            namespace=KUBERNETES_NAMESPACE,
            body=configmap
        )

        self._register_resource(ConfigMapResource(configmap=configmap))

        return configmap
        
