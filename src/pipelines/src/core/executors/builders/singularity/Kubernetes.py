import time, logging

from typing import List

from kubernetes.client.rest import ApiException
from kubernetes.client import (
    V1Job,
    V1JobSpec,
    V1VolumeMount,
    V1Volume,
    V1PodSpec,
    V1PodTemplateSpec,
    V1PersistentVolumeClaimVolumeSource,
    V1ObjectMeta,
)

from conf.configs import KUBERNETES_NAMESPACE, PIPELINES_PVC
from core.TaskResult import TaskResult
from core.resources import JobResource
from core.executors.builders.BaseBuildExecutor import BaseBuildExecutor
from core.executors.builders.singularity.helpers.ContainerBuilder import container_builder


class Kubernetes(BaseBuildExecutor):
    def execute(self, on_finish_callback) -> TaskResult:
        # Create the kaniko job return a failed task result on exception
        # with the error message as the str value of the exception
        try: 
            job = self._create_job()
        
            # Poll the job status until the job is in a terminal state
            while not self._job_in_terminal_state(job):
                job = self.batch_v1_api.read_namespaced_job(
                    job.metadata.name, KUBERNETES_NAMESPACE
                )

                time.sleep(self.polling_interval)
        except ApiException as e:
            return TaskResult(status=1, errors=[str(e)])


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
            self._store_result(".stdout", logs)

        except ApiException as e:
            logging.exception(e)

        # TODO Validate the jobs outputs against outputs in the task definition

        # TODO implement on_finish_callback

        return TaskResult(status=0 if self._job_succeeded(job) else 1)

    def _create_job(self):
        """Create a job in the Kubernetes cluster"""
        # Set the name for the k8 job metadata
        job_name = f"{self.group.id}.{self.pipeline.id}.{self.pipeline.run_id}.{self.task.id}"

        # List of volume mount objects for the container 
        volume_mounts = [
            # Volume mount for the output
            V1VolumeMount(
                name="output",
                mount_path="/mnt/",
                # sub_path=self.task.output_dir.lstrip("/mnt/pipelines/") # NOTE works
                sub_path=self.task.work_dir.lstrip("/mnt/pipelines/")
            )
        ]

        # Container object
        container = container_builder.build(
            self.task,
            volume_mounts=volume_mounts,
            directives=self.directives,
        )

        # List of volume objects
        volumes = [
            # Volume for mounting the output
            V1Volume(
                name="output",
                persistent_volume_claim=V1PersistentVolumeClaimVolumeSource(
                    claim_name=PIPELINES_PVC
                ),
            )
        ]

        # Pod template and pod template spec
        template = V1PodTemplateSpec(
            spec=V1PodSpec(
                containers=[container], restart_policy="Never", volumes=volumes
            )
        )

        # Job spec
        v1jobspec_props = {}
        if self.task.max_exec_time > 0:
            v1jobspec_props["active_deadline_seconds"] = self.task.max_exec_time

        self.task.max_retries = 0 if self.task.max_retries < 0 else self.task.max_retries
        job_spec = V1JobSpec(
            **v1jobspec_props,
            backoff_limit=self.task.max_retries,
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
                namespace=KUBERNETES_NAMESPACE, body=body
            )
        except ApiException as e:
            raise e

        # Register the job to be deleted after execution
        self._register_resource(JobResource(job=job))

        return job
