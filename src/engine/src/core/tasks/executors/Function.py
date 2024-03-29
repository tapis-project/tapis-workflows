import os, base64, time, shutil, inspect, json

from kubernetes import client

from owe_python_sdk.TaskExecutor import TaskExecutor
from owe_python_sdk.utils import get_schema_extensions
from owe_python_sdk.constants import FUNCTION_TASK_RUNTIMES, STDERR, STDOUT
from conf.constants import (
    WORKFLOW_NFS_SERVER,
    KUBERNETES_NAMESPACE,
    OWE_PYTHON_SDK_DIR,
)
from core.resources import JobResource
from utils import get_flavor
from utils.k8s import flavor_to_k8s_resource_reqs, gen_resource_name
from core.tasks import function_bootstrap
from core.repositories import GitCacheRepository


class ContainerDetails:
    def __init__(
        self,
        image,
        command,
        args,
        working_dir=None,
        env=[]
    ):
        self.image = image
        self.command = command
        self.args = args
        self.working_dir = working_dir
        self.env = env


# TODO Remove the kubernetes token from the container(s)?
class Function(TaskExecutor):
    def __init__(self, task, ctx, exchange, plugins=[]):
        TaskExecutor.__init__(self, task, ctx, exchange, plugins=plugins)

        self.runtimes = FUNCTION_TASK_RUNTIMES
        
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
        job_name = gen_resource_name(prefix="fn")
        # Prepares the file system for the Function task by clone 
        # git repsoitories specified in the request
        git_cache_repo = GitCacheRepository(cache_dir=self.task.exec_dir)
        try:
            for repo in self.task.git_repositories:
                git_cache_repo.add(repo.url, repo.directory, branch=repo.branch)
        except Exception as e:
            return self._task_result(1, errors=[str(e)])
        
        # Set up the container details for the task's specified runtime
        container_details = self._setup_container()
        
        # Job body
        body = client.V1Job(
            metadata=client.V1ObjectMeta(
                labels=dict(job=job_name),
                name=job_name,
                namespace=KUBERNETES_NAMESPACE,
            ),
            spec=client.V1JobSpec(
                backoff_limit=0 if self.task.max_retries < 0 else self.task.max_retries,
                template=client.V1PodTemplateSpec(
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=job_name,
                                command=container_details.command,
                                args=container_details.args,
                                image=container_details.image,
                                volume_mounts=[
                                    # Volume mount for the output
                                    client.V1VolumeMount(
                                        name="task-workdir",
                                        mount_path=self.task.container_work_dir, 
                                    )
                                ],
                                env=container_details.env,
                                resources=flavor_to_k8s_resource_reqs(get_flavor("c1sml"))
                            )
                        ],
                        restart_policy="Never",
                        volumes=[
                            client.V1Volume(
                                name="task-workdir",
                                nfs=client.V1NFSVolumeSource(
                                    server=WORKFLOW_NFS_SERVER,
                                    path=self.task.nfs_work_dir
                                ),
                            )
                        ]
                    )
                )
            )
        )
        
        try:
            job = self.batch_v1_api.create_namespaced_job(
                namespace=KUBERNETES_NAMESPACE,
                body=body
            )

            # Register the job to be deleted after execution
            self._register_resource(JobResource(job=job))
        except Exception as e:
            self.ctx.logger.error(e)
            return self._task_result(1, errors=[e])

        try:
            while not self._job_in_terminal_state(job):
                if self.terminating:
                    self.ctx.logger.error("Workflow Terminated")
                    self.cleanup(terminating=True)
                    self._stderr("Workflow Terminated", "w")
                    return self._task_result(2, errors=["Workflow Terminated"])

                job = self.batch_v1_api.read_namespaced_job(
                    job.metadata.name, KUBERNETES_NAMESPACE
                )

                time.sleep(self.polling_interval)
        except Exception as e:
            self.ctx.logger.error(str(e))
            self._stderr(str(e), "w")
            return self._task_result(1, errors=[e])

        return self._task_result(0 if self._job_succeeded(job) else 1)

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
                name="_OWE_TASK_ID",
                value=self.task.id
            ),
            client.V1EnvVar(
                name="_OWE_PIPELINE_ID",
                value=self.ctx.pipeline.id
            ),
            client.V1EnvVar(
                name="_OWE_PIPELINE_RUN_UUID",
                value=self.ctx.pipeline_run.uuid
            ),
            client.V1EnvVar(
                name="_OWE_WORK_DIR",
                value=self.task.container_work_dir
            ), 
            client.V1EnvVar(
                name="_OWE_INPUT_DIR",
                value=self.task.container_input_dir
            ),
            client.V1EnvVar(
                name="_OWE_OUTPUT_DIR",
                value=self.task.container_output_dir
            ),
            client.V1EnvVar(
                name="_OWE_EXEC_DIR",
                value=os.path.join(self.task.container_exec_dir)
            ),
            client.V1EnvVar(
                name="_OWE_INPUT_SCHEMA",
                value=json.dumps({
                    key: val.dict() for key, val in self.task.input.items()
                })
            )
        ]

        # Convert defined workflow inputs into the function containers env vars with
        # the open workflow engine input prefix
        container_details.env = container_details.env + env
        
        return container_details

    def _write_entrypoint_file(self, file_path, code):
        with open(file_path, "wb") as file:
            file.write(base64.b64decode(code))
    
    # FIXME
    # def _setup_linux_container(self):
    #     # Create entrypoint file that will be mounted into the container via NFS mount.
    #     # The code provided in the request is expected to be base64 encoded. Decode, then
    #     # encode in UTF-8
    #     entrypoint_filename = "entrypoint.sh"
    #     local_entrypoint_file_path = os.path.join(self.task.exec_dir, entrypoint_filename)
    #     self._write_entrypoint_file(local_entrypoint_file_path, self.task.code)

    def _setup_python_container(self):
        # Create entrypoint file that will be mounted into the container via NFS mount.
        # The code provided in the request is expected to be base64 encoded. Decode, then
        # encode in UTF-8
        entrypoint_filename = "entrypoint.py"
        local_entrypoint_file_path = os.path.join(self.task.exec_dir, entrypoint_filename)
        entrypoint_env_var = client.V1EnvVar(
            name="_OWE_ENTRYPOINT_FILE_PATH",
            value=os.path.join(self.task.container_exec_dir, entrypoint_filename)
        )

        # If the task has an entrypoint defined, set the code to be executed in the entrypoint
        # to the bootstrap code 
        if self.task.entrypoint != None:
            self.task.code = base64.b64encode(
                bytes(inspect.getsource(function_bootstrap), encoding="utf8")
            )
            entrypoint_env_var = client.V1EnvVar(
                name="_OWE_ENTRYPOINT_FILE_PATH",
                value=os.path.join(self.task.container_exec_dir, self.task.entrypoint.lstrip("/"))
            )
                
        self._write_entrypoint_file(local_entrypoint_file_path, self.task.code)

        # Create requirements file that will be mounted into the functions container
        # via NFS mount. This file will be used with the specified installer to install
        # the necessary python packages
        requirements_filename = "requirements.txt"
        local_requirements_file_path = f"{self.task.exec_dir}requirements.txt"
        has_packages = len(self.task.packages) > 0
        if has_packages:
            with open(local_requirements_file_path, "w") as file:
                file.write("\n".join(self.task.packages))
        
        # Kubernetes "command" property of V1Container
        command = ["/bin/sh", "-c"]

        # NOTE Only supporting pip for now
        # Requirements file path inside the container
        requirements_txt = os.path.join(self.task.container_exec_dir, requirements_filename)
        
        # Entrypoint path inside the container
        entrypoint_py = os.path.join(self.task.container_exec_dir, entrypoint_filename)
        
        # The output file for the install logs inside the container
        dot_install = os.path.join(self.task.container_output_dir, ".install")

        # stderr path inside the container
        stderr = os.path.join(self.task.container_output_dir, STDERR)

        # .stdout path inside the container
        stdout = os.path.join(self.task.container_output_dir, STDOUT)

        install_cmd = ""
        if has_packages:
            install_cmd = f"pip install -r {requirements_txt} 2> {stderr} 1> {dot_install} &&"

        # TODO handle for "command" property

        # Copy the owe-python-sdk files to the exec directory
        owe_python_sdk_local_path = os.path.join(self.task.work_dir, "src/owe_python_sdk")
        shutil.copytree(OWE_PYTHON_SDK_DIR, owe_python_sdk_local_path, dirs_exist_ok=True)

        entrypoint_cmd = f"python3 {entrypoint_py} 2> {stderr} 1> {stdout}"
        args = [f"{install_cmd} {entrypoint_cmd}"]

        return ContainerDetails(
            image=self.task.runtime,
            command=command,
            args=args,
            env=[entrypoint_env_var]
        )