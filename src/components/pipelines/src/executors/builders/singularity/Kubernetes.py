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
from core.ActionResult import ActionResult
from core.resources import JobResource
from executors.builders.BaseBuildExecutor import BaseBuildExecutor
from executors.builders.singularity.helpers.ContainerBuilder import container_builder


class Kubernetes(BaseBuildExecutor):
    def execute(self, on_finish_callback) -> ActionResult:
        # Create the kaniko job return a failed action result on exception
        # with the error message as the str value of the exception
        try: 
            job = self._create_job()
        except Exception as e:
            return ActionResult(status=1, errors=[str(e)])

        # Poll the job status until the job is in a terminal state
        while not self._job_in_terminal_state(job):
            job = self.batch_v1_api.read_namespaced_job(
                job.metadata.name, KUBERNETES_NAMESPACE
            )

            time.sleep(self.polling_interval)

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
            logging.debug(f"{logs}\n")
            self._store_result(".stdout", logs)

        except ApiException as e:
            logging.exception(e)

        # TODO Validate the jobs outputs against outputs in the action definition

        # TODO implement on_finish_callback

        return ActionResult(status=0 if self._job_succeeded(job) else 1)

    def _create_job(self):
        """Create a job in the Kubernetes cluster"""
        # Set the name for the k8 job metadata
        job_name = f"{self.group.id}.{self.pipeline.id}.{self.action.id}"

        # List of volume mount objects for the container 
        volume_mounts = [
            # Volume mount for the output
            V1VolumeMount(
                name="output",
                mount_path="/mnt/",
                # sub_path=self.action.output_dir.lstrip("/mnt/pipelines/") # NOTE works
                sub_path=self.action.work_dir.lstrip("/mnt/pipelines/")
            )
        ]

        # Container object
        container = container_builder.build(
            self.action,
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
        job_spec = V1JobSpec(
            backoff_limit=(self.action.retries + 1), template=template
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
        except Exception as e:
            raise e

        # Register the job to be deleted after execution
        self._register_resource(JobResource(job=job))

        return job
