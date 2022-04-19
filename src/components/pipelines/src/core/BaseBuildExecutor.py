import json, time, uuid, base64, os

from helpers.ContextResolver import context_resolver
from errors.credential import CredentialError
from conf.configs import SCRATCH_DIR


class BaseBuildExecutor:
    def _resolve_context_string(self, action):
        # Resolve the repository from which the code containing the Dockerfile
        # will be pulled
        return context_resolver.resolve(action.context)

    def _resolve_destination_string(self, action, event, directives=None):

        if action.destination == None:
            return None

        # Default to latest tag
        tag = action.destination.tag
        if tag is None:
            tag = "latest"

        # The image tag can be overwritten by specifying directives in the 
        # commit message. Image tagging directives take precedence over the
        # the image_property of the pipeline.
        if directives is not None:
            for key, value in directives.__dict__.items():
                if key == "CUSTOM_TAG" and key is not None:
                    tag = value
                elif key == "CUSTOM_TAG" and key is None:
                    tag = action.destination.tag
                elif key == "TAG_COMMIT_SHA" and event.commit_sha is not None:
                    tag = event.commit_sha
            
        destination = action.destination.url + f":{tag}"

        return destination

    def _create_dockerhub_config(self, action, pipeline):
        # Get image registry credentials from config
        credential = action.destination.credential

        if credential == None:
            raise CredentialError(
                "No credentials for the destination")

        # Create the config dir to store the credentials
        self.dockerhub_config_dir = f"{SCRATCH_DIR}/dockerhub-config-{pipeline.id}-{action.id}-{str(uuid.uuid4())}"
        os.mkdir(self.dockerhub_config_dir)

        # Base64 encode credentials
        encoded_creds = base64.b64encode(
            f"{credential.data.username}:{credential.data.token}"
                .encode("utf-8")
        )

        # Add the credentials to the config file
        registry_creds = {
            "auths": {
                "https://index.docker.io/v1/": {
                    "auth": encoded_creds.decode("utf-8")
                }
            }
        }

        # Create the .docker/config.json file that will be mounted to the
        # kaniko container and write the registry credentials to it
        with open(f"{self.dockerhub_config_dir}/config.json", "w") as file:
            file.write(json.dumps(registry_creds))