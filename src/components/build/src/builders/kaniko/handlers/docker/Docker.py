import json, uuid, time, os, base64

import docker

from core.AbstractBuildHandler import AbstractBuildHandler
from helpers.ContextResolver import context_resolver
# from helpers.DestinationResolver import destination_resolver
from errors.credential import CredentialError
from utils.attrs import has_one_of


class Docker(AbstractBuildHandler):
    def __init__(self):
        self.config_file = None
        self.can_build = False
        self.can_deploy = False
        self.can_cache = False
        self.build_succeeded = False

    def handle(self, build_context):
        deployment = build_context.deployment
        directives = build_context.directives

        # Determines whether the build service can build, deploy or
        # cache the image. Caching handled by kaniko
        self._set_flags(deployment, directives)

        # Do not build if there is no BUILD or DEPLOY directive and
        # the auto_build and auto_deploy flags are set to False
        if self.can_build == False:
            print("Build cancelled. No 'build' or 'deploy' directive found.")
            self.reset()
            return

        # Create a docker client
        client = docker.from_env()
        
        # Generate the credentials config that kaniko will use to push the
        # image to an image registry
        self.generate_config(deployment)

        # Set the repository from which the code containing the Dockerfile
        # will be pulled
        context = context_resolver.resolve(build_context.deployment.context)

        # Set the image registry to which the image will be pushed after build
        destination = self.resolve_destination(build_context, directives)

        # Build the entrypoint for the kaniko executor based on the deployment
        # and directives
        # TODO implement entrypoint_builder
        entrypoint = (
            "/kaniko/executor" +
            f" --cache={'true' if self.can_cache else 'false'}" +
            f" --context {context}" +
            (f" --context-sub-path {deployment.context_sub_path}"
                if deployment.context.sub_path is not None else "") +
            f" --dockerfile {deployment.context.dockerfile_path}" +
            (f" --destination {destination}"
                if deployment.destination is not None else f" --no-push") +
            (f" --git branch={deployment.branch}"
                if deployment.branch is not None else "")
        )

        print(f"Build start started for deployment {deployment.name}:{deployment.id}")

        # Run the kaniko build
        container = client.containers.run(
            "gcr.io/kaniko-project/executor:debug",
            volumes={
                self.config_file: {"bind": "/kaniko/.docker/config.json", "mode": "ro"},
                "kaniko-data": {"bind": "/kaniko-data/", "mode": "rw"}
            },
            detach=True,
            entrypoint=entrypoint,
            stderr=True,
            stdout=True,
        )

        # TODO Update the build status to "in_progress"

        # Waits until the container is finished running to return the
        # result that contains the status code and the error
        result = dict(container.wait().items())

        logs = self._get_container_logs(client, container)

        for log in logs:
            print(log)

        print(f"Build ended for deployment {deployment.name}:{deployment.id}")
        if result["StatusCode"] == 0:
            self.build_succeeded = True

        status = "fail"
        if self.build_succeeded:
            status = "success"
        
        print(f"Build status: {status}")

        # Remove the container and reset the builder
        container.remove()

        # Handle post build deployment
        if self.can_deploy:
            self.deploy(deployment)

        self.reset(delete_config=True)

    def deploy(self, deployment):
        print(f"Deployment started for {deployment.name}:{deployment.id}")
        # TODO Implement post-build deployment
        status = "success"
        print(f"Deployment ended for {deployment.name}:{deployment.id}")
        print(f"Deployment status: {status}")
 
    def generate_config(self, deployment):
        # Get image registry credentials from config
        credential = deployment.destination.credential

        if credential == None:
            raise CredentialError(
                "No credentials for the destination")

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
        self.can_build = False
        self.can_deploy = False
        self.can_cache = False
        self.build_succeeded = False
        
    def resolve_destination(self, build_context, directives=None):
        # If an image tag is provided, tag the image
        deployment = build_context.deployment
        event = build_context.event

        # Default to latest tag
        tag = deployment.destination.tag
        if tag is None:
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
            
        destination = deployment.destination.url + f":{tag}"

        return destination
    
    def _cred_filter(self, credential):
        if credential.type == "image_registry":
            return True
        return False

    def _get_container_logs(self, client, container):
        logs = []
        iterator = client.containers.get(container.name).logs(stream=True, follow=False)
        try:
            while True:
                logs.append(next(iterator).decode("utf-8").rstrip())
        except StopIteration:
            pass

        return logs

    def _set_flags(self, deployment, directives):
        # Set the can_build flag
        self.can_build = (
            has_one_of(directives, ["BUILD", "DEPLOY"])
            or deployment.auto_build
            or deployment.auto_deploy
        )

        # Set the can_deploy flag
        self.can_deploy = (
            hasattr(directives, "DEPLOY")
            or deployment.auto_deploy
        )

        # Set the cache flag to indicate whether kaniko should cache the image
        self.can_cache = deployment.cache or hasattr(directives, "CACHE")

handler = Docker()