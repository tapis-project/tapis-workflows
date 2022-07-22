import json, base64, os

from executors.builders.helpers.ContextResolver import context_resolver
from errors.credentials import CredentialsError
from core.TaskExecutor import TaskExecutor


class BaseBuildExecutor(TaskExecutor):
    def __init__(self, task, message):
        TaskExecutor.__init__(self, task, message)

    def _resolve_context_string(self):
        # Resolve the repository from which the code containing the Dockerfile
        # will be pulled
        return context_resolver.resolve(self.task.context)

    def _resolve_destination_string(self):
        if self.task.destination == None:
            return None

        # Default to latest tag
        tag = self.task.destination.tag
        if tag is None:
            tag = "latest"

        # The image tag can be overwritten by specifying directives in the
        # commit message. Image tagging directives take precedence over the
        # the image_property of the pipeline.
        if self.directives is not None:
            for key, value in self.directives.__dict__.items():
                if key == "CUSTOM_TAG" and key is not None:
                    tag = value
                elif key == "CUSTOM_TAG" and key is None:
                    tag = self.task.destination.tag
                elif key == "TAG_COMMIT_SHA" and self.event.commit_sha is not None:
                    tag = self.event.commit_sha

        destination = self.task.destination.url + f":{tag}"

        return destination

    def _create_dockerhub_config(self):
        # Get image registry credentials
        credentials = self.task.destination.credentials
        if credentials == None:
            raise CredentialsError("No credentials for the destination")

        # Create the config dir to store the credentials
        self.dockerhub_config_dir = f"{self.task.scratch_dir}dockerhub/"
        os.mkdir(self.dockerhub_config_dir)

        # Base64 encode credentials
        encoded_creds = base64.b64encode(
            f"{credentials.data.username}:{credentials.data.token}".encode("utf-8")
        )

        # Add the credentials to the config file
        registry_creds = {
            "auths": {
                "https://index.docker.io/v1/": {"auth": encoded_creds.decode("utf-8")}
            }
        }

        # Create the .docker/config.json file that will be mounted to the
        # kaniko container and write the registry credentials to it
        dockerhub_config_file = f"{self.dockerhub_config_dir}config.json"
        with open(dockerhub_config_file, "w") as file:
            file.write(json.dumps(registry_creds))
