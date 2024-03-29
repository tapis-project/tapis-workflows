import logging

from kubernetes import client

from owe_python_sdk.TaskExecutor import TaskExecutor
from conf.constants import KUBERNETES_NAMESPACE
from core.resources import PodResource
from utils import get_flavor
from utils.k8s import flavor_to_k8s_resource_reqs, gen_resource_name


# TODO Review the Kubernetes attack surface guide.
# TODO Remove the kubernetes token from the container(s)
class Application(TaskExecutor):
    def execute(self):
        """Create a the container"""
        container_name = gen_resource_name()
        # List of volume mount objects for the container
        volume_mounts = [
            # Volume mount for the output
            client.V1VolumeMount(
                name="artifacts",
                mount_path="/mnt/",
                sub_path=self.task.nfs_output_dir
            ),
        ]

        # Container object
        container = client.V1Container(
            name=container_name,
            image=self._resovle_image(),
            args=self._resolve_args(),
            volume_mounts=volume_mounts,
            resources=flavor_to_k8s_resource_reqs(get_flavor("c1lrg"))
        )

        # Volume for output and caching
        volumes = [
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


