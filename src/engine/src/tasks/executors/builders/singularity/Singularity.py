import time, logging

from kubernetes.client.rest import ApiException
from kubernetes.client import (
    V1Job,
    V1JobSpec,
    V1VolumeMount,
    V1Volume,
    V1PodSpec,
    V1PodTemplateSpec,
    V1NFSVolumeSource,
    V1ObjectMeta,
)

from conf.constants import KUBERNETES_NAMESPACE, WORKFLOW_NFS_SERVER
from resources import JobResource
from tasks.BaseBuildExecutor import BaseBuildExecutor
from tasks.executors.builders.singularity.helpers.ContainerBuilder import container_builder
from errors import WorkflowTerminated
from utils.k8s import gen_resource_name

class Singularity(BaseBuildExecutor):
    def __init__(self, task, ctx, exchange, plugins=[]):
        BaseBuildExecutor.__init__(self, task, ctx, exchange, plugins=plugins)

        self._container_singularity_cache_dir = "/tmp/cache"
        
    def execute(self):
        # Create the kaniko job return a failed task result on exception
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
            self.cleanup(terminating=True)
            return self._task_result(2, errors=[e])
        except ApiException as e:
            return self._task_result(1, errors=[str(e)])


        # Get the job's pods name
        pod_name = self.core_v1_api.list_namespaced_pod(
            namespace=KUBERNETES_NAMESPACE,
            label_selector=f"job-name={job.metadata.name}"
        ).items[0].metadata.name
        
        # Get the logs(stdout) from this job's pod
        logs = None
        try:
            logs = self.core_v1_api.read_namespaced_pod_log(
                name=pod_name,
                namespace=KUBERNETES_NAMESPACE,
                _return_http_data_only=True,
                _preload_content=False,
            ).data  # .decode("utf-8")
            # logging.debug(f"{logs}\n") # TODO Remove
            self._stdout(logs)

        except ApiException as e:
            logging.exception(e)

        # TODO Validate the jobs outputs against outputs in the task definition

        # TODO implement on_finish_callback

        return self._task_result(0 if self._job_succeeded(job) else 1)

    def _create_job(self):
        """Create a job in the Kubernetes cluster"""
        # Set the name for the k8 job metadata
        job_name = gen_resource_name(prefix="sib")
        
        # List of volume mount objects for the container 
        volume_mounts = [
            # Volume mount for the workdir
            V1VolumeMount(
                name="task-workdir",
                mount_path=self.task.container_work_dir
            ),
            # Volume mount the task-workdir
            V1VolumeMount(
                name="singularity-cache",
                mount_path=self._container_singularity_cache_dir,
            )
        ]

        # Container object
        container = container_builder.build(
            self.task,
            volume_mounts=volume_mounts,
            directives=self.directives,
            cache_dir=self._container_singularity_cache_dir
        )

        # List of volume objects
        volumes = [
            # Volume for mounting the output
            V1Volume(
                name="task-workdir",
                nfs=V1NFSVolumeSource(
                    server=WORKFLOW_NFS_SERVER,
                    path=self.task.nfs_work_dir
                ),
            ),
            V1Volume(
                name="singularity-cache",
                nfs=V1NFSVolumeSource(
                    server=WORKFLOW_NFS_SERVER,
                    path=self.pipeline.nfs_singularity_cache_dir
                ),
            )
        ]

        # Pod template and pod template spec
        template = V1PodTemplateSpec(
            spec=V1PodSpec(
                automount_service_account_token=False,
                containers=[container],
                restart_policy="Never",
                volumes=volumes
            )
        )

        # Job spec
        v1jobspec_props = {}
        if self.task.execution_profile.max_exec_time > 0:
            v1jobspec_props["active_deadline_seconds"] = self.task.execution_profile.max_exec_time

        self.task.execution_profile.max_retries = 0 if self.task.execution_profile.max_retries < 0 else self.task.execution_profile.max_retries
        job_spec = V1JobSpec(
            **v1jobspec_props,
            backoff_limit=self.task.execution_profile.max_retries,
            template=template
        )

        # Job metadata
        metadata = V1ObjectMeta(
            labels=dict(job=job_name),
            name=job_name,
            namespace=KUBERNETES_NAMESPACE,
        )

        # Job body
        body = V1Job(metadata=metadata, spec=job_spec)
        
        try:
            job = self.batch_v1_api.create_namespaced_job(
                namespace=KUBERNETES_NAMESPACE,
                body=body
            )
        except ApiException as e:
            raise e

        # Register the job to be deleted after execution
        self._register_resource(JobResource(job=job))

        return job
