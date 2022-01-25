import json, uuid, time, os, base64

import docker

from core.AbstractBuildHandler import AbstractBuildHandler
from errors.errors import CredentialError
from utils.attrs import has_one_of


class Docker(AbstractBuildHandler):
    def __init__(self):
        self.config_file = None

    def handle(self, build_context):
        deployment = build_context.deployment
        directives = build_context.directives

        # Do not build if there is no DEPLOY directive
        if (
            deployment.auto_deploy == False 
            and has_one_of(directives, [ "BUILD", "DEPLOY" ]) == False
        ):
            print("Build cancelled. No 'deploy' directive found.")
            self.reset()
            return

        # Create a docker client
        client = docker.from_env()
        
        # Generate config script
        self.generate_config(deployment)

        # Build destiniation
        destination = self.resolve_destination(build_context, directives)

        # Build the cmd for kaniko based on the deployment.
        kaniko_cmd = (
            "/kaniko/executor" +
            " --cache=false" +
            f" --context {deployment.context}" +
            (f" --context-sub-path {deployment.context_sub_path}"
                if deployment.context_sub_path is not None else "") +
            f" --dockerfile {deployment.dockerfile_path}" +
            (f" --destination {destination}"
                if deployment.destination is not None else f" --no-push") +
            (f" --git branch={deployment.branch}"
                if deployment.branch is not None else "")
        )

        # Run the kaniko build
        print(f"Starting build: Deployment {deployment.name}:{deployment.id}")
        container = client.containers.run(
            "gcr.io/kaniko-project/executor:debug",
            volumes={
                self.config_file: {"bind": "/kaniko/.docker/config.json", "mode": "ro"},
                "kaniko-data": {"bind": "/kaniko-data/", "mode": "rw"}
            },
            detach=True,
            entrypoint=kaniko_cmd,
            auto_remove=True,
            stderr=True,
            stdout=True,
        ).wait()

        print(dir(container))

        self.reset(delete_config=True)

    def generate_config(self, deployment):
        # Get image registry credentials from config
        creds = list(filter(self._cred_filter, deployment.deployment_credentials))

        if len(creds) == 0:
            raise CredentialError(
                "No credentials found with type 'image_registry' for this deployment")

        # Take the first image registry credential available. There should only be one.
        credential = creds[0].credential

        # Create the config file to store the credentials temporarily
        self.config_file = f"/tmp/docker-config-{time.time() * 1000}-{str(uuid.uuid4())}.json"

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
        with open(self.config_file, "w") as file:
            file.write(json.dumps(registry_creds))

    def reset(self, delete_config=False):
        # Delete the config file
        if delete_config:
            os.remove(self.config_file)

        self.config_file = None

    def resolve_destination(self, build_context, directives=None):
        # If an image tag is provided, tag the image
        deployment = build_context.deployment
        event = build_context.event


        tag = deployment.image_tag
        if deployment.image_tag is None:
            tag = "latest"

        # The image tag can be overwritten by specifying directives in the 
        # commit message. Image tagging directives take precedence over the
        # the image_property of the deployment.
        if directives is not None:
            for key, value in directives.__dict__.items():
                if key == "CUSTOM_TAG" and key is not None:
                    tag = value
                elif key == "CUSTOM_TAG" and key is None:
                    tag = deployment.image_tag
                elif key == "TAG_COMMIT_SHA":
                    tag = event.commit_sha
            
        destination = deployment.destination + f":{tag}"

        return destination
    
    def _cred_filter(self, credential):
        if credential.type == "image_registry":
            return True
        return False

handler = Docker()