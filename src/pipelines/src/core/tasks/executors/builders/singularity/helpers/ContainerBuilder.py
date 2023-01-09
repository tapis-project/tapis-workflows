import logging, os

# log CRITICAL messages
logging.getLogger("git").setLevel(logging.CRITICAL)
import git

from kubernetes.client import V1Container, V1EnvVar

from conf.constants import SINGULARITY_IMAGE_URL, SINGULARITY_IMAGE_TAG


class ContainerBuilder:
    def build(self, task, volume_mounts=[], directives=None):

        command = self.resolve_command(task, directives=directives)

        container = V1Container(
            name="singularity",
            env=self.resolve_env(task),
            image=f"{SINGULARITY_IMAGE_URL}:{SINGULARITY_IMAGE_TAG}",
            command=command,
            volume_mounts=volume_mounts,
        )

        return container

    def resolve_command(self, task, directives=None):

        # Pull the image from Dockerhub and generate the SIF file
        if task.context.type == "dockerhub":
            cmd = [
                "singularity",
                "pull",
                "--dir=/mnt/output/",
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
                token = f"{task.context.credentials.data.personal_access_token}@"

            # Pull the git repository with the recipe file
            repo = os.path.join(f"https://{token}github.com", task.context.url) + ".git"
            
            git.Repo.clone_from(
                repo,
                task.scratch_dir,
                branch=task.context.branch
            )

            # Recipe file path is the scratch dir + recipe file path specified
            # in the context
            recipe_file_path = os.path.join(
                "/mnt/scratch/",
                task.context.recipe_file_path
            )

            # Build the command
            command = [
                "singularity",
                "build",
                f"/mnt/output/{task.destination.filename or ''}",
                recipe_file_path
            ]

            return command

    def resolve_env(self, task):
        # Add the dockerhub username and access token
        if task.destination.type == "dockerhub":
            return [
                V1EnvVar(
                    name="SINGULARITY_DOCKERHUB_USERNAME",
                    value=task.destination.credentials.data.username
                ),
                V1EnvVar(
                    name="SINGULARITY_DOCKERHUB_PASSOWORD",
                    value=task.destination.credentials.data.token
                )
            ]

        # return an empty array by default
        return []
        
container_builder = ContainerBuilder()