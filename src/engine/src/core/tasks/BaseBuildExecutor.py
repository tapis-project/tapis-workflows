import json, base64, os

from core.tasks.executors.builders.helpers.ContextResolver import context_resolver
from errors.credentials import CredentialsError
from core.tasks.TaskExecutor import TaskExecutor

# TODO Move methods of this class to helpers, use the helpers in decendent classes,
# and delete once complete
class BaseBuildExecutor(TaskExecutor):
    def __init__(self, task, ctx, exchange, plugins=[]):
        TaskExecutor.__init__(self, task, ctx, exchange, plugins=plugins)

    def _resolve_context_string(self):
        # Resolve the repository from which the code containing the Dockerfile
        # will be pulled
        return context_resolver.resolve(self.task.context)

    def _resolve_destination_string(self):
        if self.task.destination == None:
            return None

        # Default to latest tag
        tag = ""
        if self.task.destination.tag != None:
            tag = f":{self.task.destination.tag}"

        destination = f"{self.task.destination.url}{tag}"

        return destination

    def _create_dockerhub_config(self):
        # Get image registry credentials
        credentials = self.task.destination.credentials
        if credentials == None:
            raise CredentialsError("No credentials for the destination")

        # Create the config dir to store the credentials
        self.dockerhub_config_dir = f"{self.task.exec_dir}dockerhub/"
        os.mkdir(self.dockerhub_config_dir)

        # Base64 encode credentials
        encoded_creds = base64.b64encode(
            f"{credentials.username}:{credentials.token}".encode("utf-8")
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
