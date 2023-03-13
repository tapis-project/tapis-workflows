import logging

from uuid import uuid4

from kubernetes import client

from core.tasks.TaskExecutor import TaskExecutor
from conf.constants import PIPELINES_PVC, KUBERNETES_NAMESPACE, FLAVOR_C1_MEDIUM
from core.resources import PodResource
from utils.k8s import get_k8s_resource_reqs


# TODO Review the Kubernetes attack surface guide.
# TODO Remove the kubernetes token from the container(s)
class ContainerRun(TaskExecutor):
    def execute(self):
        """Create a the container"""
        container_name = str(uuid4())
        # List of volume mount objects for the container
        volume_mounts = [
            # Volume mount for the output
            client.V1VolumeMount(
                name="artifacts",
                mount_path="/mnt/",
                sub_path=self.task.output_dir.replace("/mnt/pipelines/", "") 
            ),
        ]

        # Container object
        container = client.V1Container(
            name=container_name,
            image=self._resovle_image(),
            args=self._resolve_args(),
            volume_mounts=volume_mounts,
            resources=get_k8s_resource_reqs(FLAVOR_C1_MEDIUM)
        )

        # Volume for output and caching
        volumes = [
            client.V1Volume(
                name="artifacts",
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                    claim_name=PIPELINES_PVC
                ),
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
        self.task.max_retries = 0 if self.task.max_retries < 0 else self.task.max_retries
        job_spec = client.V1PodSpec(
            backoff_limit=(self.task.max_retries), template=template)

        # Job metadata
        metadata = client.V1ObjectMeta(
            labels=dict(container_name=container_name),
            name=container_name,
            namespace=KUBERNETES_NAMESPACE,
        )

        # Job body
        body = client.V1Pod(metadata=metadata, spec=job_spec)
        
        try:
            pod = self.batch_v1_api.create_namespaced_pod(
                namespace=KUBERNETES_NAMESPACE, body=body
            )
        except Exception as e:
            logging.critical(e)
            raise e

        # Register the job to be deleted after execution
        self._register_resource(PodResource(pod=pod))

        # TODO How to check terminal state of pod

    def _resolve_image(self):
        # TODO Evaluate the image value to see if it contains a variable
        # and perform substitution
        return self.task.image

    def _resolve_args(self):
        # TODO handle container args
        return []


