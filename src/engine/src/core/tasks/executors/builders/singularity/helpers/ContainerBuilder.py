import logging, os

# log CRITICAL messages
logging.getLogger("git").setLevel(logging.CRITICAL)
import git

from kubernetes.client import V1Container, V1EnvVar

from conf.constants import SINGULARITY_IMAGE_URL, SINGULARITY_IMAGE_TAG
from utils import get_flavor
from utils.k8s import flavor_to_k8s_resource_reqs


class ContainerBuilder:
    def build(self, task, volume_mounts=[], directives=None, cache_dir="/tmp/cache"):

        command = self.resolve_command(task, directives=directives)

        container = V1Container(
            name="singularity",
            env=self.resolve_env(task, cache_dir),
            image=f"{SINGULARITY_IMAGE_URL}:{SINGULARITY_IMAGE_TAG}",
            command=command,
            volume_mounts=volume_mounts,
            resources=flavor_to_k8s_resource_reqs(get_flavor("c1lrg"))
        )

        return container

    def resolve_command(self, task, directives=None):
        # Pull the image from Dockerhub and generate the SIF file
        if task.context.type == "dockerhub":
            cmd = [
                "singularity",
                "pull",
                f"--dir={task.container_work_dir}/output",
            ]

            # Save to image.sif if no file name provided
            if task.destination.filename != None:
                cmd.append(task.destination.filename)

            # Use latest tag if not specified
            tag = "latest"
            if task.context.tag != None:
                tag = task.context.tag

            cmd.append(f"docker://{task.context.url}:{tag}")
            
            return cmd

        # Pull the Singularity file from a github repository and then build the SIF
        # file
        if task.context.type == "github":
            # Add the token to the repository url
            token = ""
            if task.context.visibility == "private":
                token = f"{task.context.credentials.personal_access_token}@"

            # Pull the git repository with the build file
            repo = os.path.join(f"https://{token}github.com", task.context.url) + ".git"
            
            git.Repo.clone_from(
                repo,
                task.exec_dir,
                branch=task.context.branch
            )
    
            # Build file path is the exec dir + build file path specified
            # in the context
            build_file_path = os.path.join(
                f"{task.container_work_dir}/exec/",
                task.context.build_file_path
            )

            # Build the command
            command = [
                "singularity",
                "build",
                f"{task.container_work_dir}/output/{task.destination.filename or ''}",
                build_file_path
            ]

            return command

    def resolve_env(self, task, cache_dir):
        k8s_envvars = []

        # Set the cache dir for Singularity
        k8s_envvars.append(
            V1EnvVar(
                name="SINGULARITY_CACHEDIR",
                value=cache_dir
            ),
        )

        # Add the dockerhub username and access token
        if task.destination.type == "dockerhub":
            k8s_envvars = k8s_envvars + [
                V1EnvVar(
                    name="SINGULARITY_DOCKERHUB_USERNAME",
                    value=task.destination.credentials.username
                ),
                V1EnvVar(
                    name="SINGULARITY_DOCKERHUB_PASSOWORD",
                    value=task.destination.credentials.token
                )
            ]

        # return an empty array by default
        return k8s_envvars
        
container_builder = ContainerBuilder()