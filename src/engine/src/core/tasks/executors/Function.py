import logging, os, base64, time, shutil

from uuid import uuid4

from kubernetes import client

from core.tasks.TaskExecutor import TaskExecutor
from owe_python_sdk.TaskResult import TaskResult
from owe_python_sdk.utils import get_schema_extensions
from conf.constants import (
    WORKFLOW_NFS_SERVER,
    KUBERNETES_NAMESPACE,
    OWE_PYTHON_SDK_DIR,
)
from core.resources import JobResource
from utils import get_flavor
from utils.k8s import flavor_to_k8s_resource_reqs, input_to_k8s_env_vars
from errors import WorkflowTerminated

class ContainerDetails:
    def __init__(
        self,
        image,
        command,
        args,
        env=None
    ):
        self.image = image
        self.command = command
        self.args = args
        self.env = env


# TODO Review the Kubernetes attack surface guide.
# TODO Remove the kubernetes token from the container(s)?
class Function(TaskExecutor):
    def __init__(self, task, ctx, exchange, plugins=[]):
        TaskExecutor.__init__(self, task, ctx, exchange, plugins=plugins)

        self.runtimes = {
            "python": ["python:3.9"]
        }
        
        # Add additional Function task runtimes from plugins
        schemas = get_schema_extensions(self.plugins, "task_executor", sub_type="function")
        for schema in schemas:
            additional_runtimes = schema.get("runtimes", {})
            for language in additional_runtimes:
                runtimes_for_language = self.runtimes.get(
                    language, []
                ) + additional_runtimes.get(language, [])
                self.runtimes[language] = runtimes_for_language

    def execute(self):
        """Create and run the container"""
        job_name = "wf-fn-" + str(uuid4())

        # List of volume mount objects for the container
        volume_mounts = [
            # Volume mount for the output
            client.V1VolumeMount(
                name="workdir",
                mount_path=self.task.container_work_dir, 
            )
        ]

        # Set up the container details for the task"s specified runtime
        container_details = self._setup_container()
        
        # Container object
        container = client.V1Container(
            name=job_name,
            command=container_details.command,
            args=container_details.args,
            image=container_details.image,
            volume_mounts=volume_mounts,
            env=container_details.env,
            resources=(flavor_to_k8s_resource_reqs(get_flavor("c1sml")))
        )

        # Volume for output
        volumes = [
            client.V1Volume(
                name="workdir",
                nfs=client.V1NFSVolumeSource(
                    server=WORKFLOW_NFS_SERVER,
                    path=self.task.work_dir.replace("/mnt/pipelines/", "/")
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

            # Register the job to be deleted after execution
            self._register_resource(JobResource(job=job))
        except Exception as e:
            logging.critical(e)
            raise e
        try:
            while not self._job_in_terminal_state(job):
                if self.terminating:
                    raise WorkflowTerminated()
                job = self.batch_v1_api.read_namespaced_job(
                    job.metadata.name, KUBERNETES_NAMESPACE
                )

                time.sleep(self.polling_interval)
        except WorkflowTerminated as e:
            self.ctx.logger.error(str(e))
            self.cleanup(terminating=True)
            return TaskResult(status=2, errors=[e])
        except Exception as e:
            self.ctx.logger.error(str(e))
            return TaskResult(status=1, errors=[e])

        return TaskResult(status=0 if self._job_succeeded(job) else 1)

    def _setup_container(self) -> ContainerDetails:
        if self.task.runtime in self.runtimes["python"]:
            container_details = self._setup_python_container()
        # elif self.task.runtime in ["node:18"]:
        #     return "entrypoint.js"
        else:
            raise Exception(f"Invalid runtime: {self.task.runtime}")

         # Set up env vars for the container
        env = [
            client.V1EnvVar(
                name="OWE_OUTPUT_DIR",
                value=os.path.join(self.task.container_work_dir, "output")
            ),
            client.V1EnvVar(
                name="OWE_SCRATCH_DIR",
                value=os.path.join(self.task.container_work_dir, "scratch")
            ),
        ]

        # Convert defined workflow inputs into the function containers env vars with
        # the open workflow engine input prefix
        container_details.env = env + input_to_k8s_env_vars(
            self.task.input,
            self.ctx,
            prefix="_OWE_WORKFLOW_INPUT_"
        )
        
        return container_details
        

    def _write_entrypoint_file(self, file_path, code):
        with open(file_path, "wb") as file:
            file.write(base64.b64decode(code))

    def _setup_python_container(self):
        # Create entrypoint file that will be mounted into the container via NFS mount.
        # The code provided in the request is expected to be base64 encoded. Decode, then
        # encode in UTF-8
        entrypoint_filename = "entrypoint.py"
        local_entrypoint_file_path = f"{self.task.scratch_dir}{entrypoint_filename}"
        self._write_entrypoint_file(local_entrypoint_file_path, self.task.code)
        
        # Create requirements file that will be mounted into the functions container
        # via NFS mount. This file will be used with the specified installer to install
        # the necessary python packages
        requirements_filename = "requirements.txt"
        local_requirements_file_path = f"{self.task.scratch_dir}requirements.txt"
        has_packages = len(self.task.packages) > 0
        if has_packages:
            with open(local_requirements_file_path, "w") as file:
                file.write("\n".join(self.task.packages))
        
        # Kubernetes "command" property of V1Container
        command = ["/bin/sh", "-c"]

        # NOTE Only supporting pip for now
        # Requirements file path inside the container
        requirements_txt = os.path.join(self.task.container_work_dir, "scratch", requirements_filename)
        
        # Entrypoint path inside the container
        entrypoint_py = os.path.join(self.task.container_work_dir, "scratch", entrypoint_filename)
        
        # The output file for the install logs inside the container
        dot_install = os.path.join(self.task.container_work_dir, "output", ".install")

        # .stderr path inside the container
        stderr = os.path.join(self.task.container_work_dir, "output", ".stderr")

        # .stdout path inside the container
        stdout = os.path.join(self.task.container_work_dir, "output", ".stdout")

        install_cmd = ""
        if has_packages:
            install_cmd = f"pip install -r {requirements_txt} 2> {stderr} 1> {dot_install} &&"

        # TODO handle for "command" property

        # Copy the owe-python-sdk files to the scratch directory
        owe_python_sdk_local_path = os.path.join(self.task.work_dir, "scratch/owe_python_sdk")
        shutil.copytree(OWE_PYTHON_SDK_DIR, owe_python_sdk_local_path, dirs_exist_ok=True)

        entrypoint_cmd = f"python3 {entrypoint_py} 2> {stderr} 1> {stdout}"
        args = [f"{install_cmd} {entrypoint_cmd}"]

        return ContainerDetails(
            image=self.task.runtime,
            command=command,
            args=args
        )