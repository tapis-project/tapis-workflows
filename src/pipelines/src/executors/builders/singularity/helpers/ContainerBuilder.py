import git, os, logging

from kubernetes.client import V1Container, V1EnvVar

from conf.configs import SINGULARITY_IMAGE_URL, SINGULARITY_IMAGE_TAG


class ContainerBuilder:
    def build(self, action, volume_mounts=[], directives=None):

        command = self.resolve_command(action, directives=directives)

        container = V1Container(
            name="singularity",
            env=self.resolve_env(action),
            image=f"{SINGULARITY_IMAGE_URL}:{SINGULARITY_IMAGE_TAG}",
            command=command,
            volume_mounts=volume_mounts,
        )

        return container

    def resolve_command(self, action, directives=None):
        # Save to image.sif if no file name provided
        filename = "image.sif"
        if action.destination.filename != None:
            filename = action.destination.filename

        # Pull the image from dockerhub and generate the SIF file
        if action.context.type == "dockerhub":
            # Use latest tag if not specified
            tag = "latest"
            if action.context.tag != None:
                tag = action.context.tag
            
            return [
                "singularity",
                "pull",
                "--dir=/mnt/output/",
                filename,
                f"docker://{action.context.url}:{tag}"
            ]

        if action.context.type == "github":
            # Add the token to the repository url
            token = ""
            if action.context.visibility == "private":
                token = f"{action.context.credentials.data.personal_access_token}@"

            # Pull the git repository with the recipe file
            repo = os.path.join(f"https://{token}github.com", action.context.url) + ".git"
            
            git.Repo.clone_from(
                repo,
                action.scratch_dir,
                branch=action.context.branch
            )

            # Recipe file path is the scratch dir + recipe file path specified
            # in the context
            recipe_file_path = os.path.join(
                "/mnt/scratch/",
                action.context.recipe_file_path
            )

            # Build the command
            command = [
                "singularity",
                "build",
                f"/mnt/output/{filename}",
                recipe_file_path
            ]

            return command

    def resolve_env(self, action):
        # Add the dockerhub username and access token
        if action.destination.type == "dockerhub":
            return [
                V1EnvVar(
                    name="SINGULARITY_DOCKERHUB_USERNAME",
                    value=action.destination.credentials.data.username
                ),
                V1EnvVar(
                    name="SINGULARITY_DOCKERHUB_PASSOWORD",
                    value=action.destination.credentials.data.token
                )
            ]

        # return an empty array by default
        return []
        
container_builder = ContainerBuilder()