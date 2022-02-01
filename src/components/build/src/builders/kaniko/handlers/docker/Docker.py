import json, uuid, time, os, base64

import docker

from core.AbstractBuildHandler import AbstractBuildHandler
from helpers.ContextResolver import context_resolver
# from helpers.DestinationResolver import destination_resolver
from helpers.ActionDispatcher import action_dispatcher
from errors.credential import CredentialError
from utils.attrs import has_one_of


class Docker(AbstractBuildHandler):
    def __init__(self):
        self.config_file = None
        self.can_build = False
        self.can_cache = False
        self.build_succeeded = False

    def handle(self, build_context):
        pipeline = build_context.pipeline
        directives = build_context.directives

        # Determines whether the build service can build or
        # cache the image. Caching handled by kaniko
        self._set_flags(pipeline, directives)

        # Do not build if there is no BUILD directive and
        # the auto_build flag set to False
        if self.can_build == False:
            print("Build cancelled. No 'build' directive found.")
            self.reset()
            return

        # Create a docker client
        client = docker.from_env()
        
        # Generate the credentials config that kaniko will use to push the
        # image to an image registry
        self.generate_config(pipeline)

        # Set the repository from which the code containing the Dockerfile
        # will be pulled
        context = context_resolver.resolve(build_context.pipeline.context)

        # Set the image registry to which the image will be pushed after build
        destination = self.resolve_destination(build_context, directives)

        # Build the entrypoint for the kaniko executor based on the pipeline
        # and directives
        # TODO implement entrypoint_builder
        entrypoint = (
            "/kaniko/executor" +
            f" --cache={'true' if self.can_cache else 'false'}" +
            f" --context {context}" +
            (f" --context-sub-path {pipeline.context_sub_path}"
                if pipeline.context.sub_path is not None else "") +
            f" --dockerfile {pipeline.context.dockerfile_path}" +
            (f" --destination {destination}"
                if pipeline.destination is not None else f" --no-push") +
            (f" --git branch={pipeline.branch}"
                if pipeline.branch is not None else "")
        )

        print(f"Build action started for pipeline {pipeline.name}:{pipeline.id}")

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

        build_status = result["StatusCode"]
        if build_status == 0:
            self.build_succeeded = True

        # Remove the container and reset the builder
        container.remove()

        # Handle post build pipeline actions
        if self.build_succeeded:
            self.run_actions(pipeline)

        self.reset(delete_config=True)

    def run_actions(self, pipeline):
        print(f"Post-build actions for Pipeline {pipeline.name}:{pipeline.id}")
        # Get post build actions
        actions = list(filter(lambda a: a.stage == "post_build", pipeline.actions))

        if len(actions) == 0:
            return
        
        for action in actions:
            print(f"Action '{action.name}' start:")
            status = action_dispatcher.dispatch(action)
            print(f"Action '{action.name}' {self._status_to_text(status)}")

 
    def generate_config(self, pipeline):
        # Get image registry credentials from config
        credential = pipeline.destination.credential

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
        self.can_cache = False
        self.build_succeeded = False
        
    def resolve_destination(self, build_context, directives=None):
        # If an image tag is provided, tag the image
        pipeline = build_context.pipeline
        event = build_context.event

        # Default to latest tag
        tag = pipeline.destination.tag
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
                    tag = pipeline.image_tag
                elif key == "COMMIT_DESTINATION":
                    tag = event.commit_sha
            
        destination = pipeline.destination.url + f":{tag}"

        return destination

    def _get_container_logs(self, client, container):
        logs = []
        iterator = client.containers.get(container.name).logs(stream=True, follow=False)
        try:
            while True:
                logs.append(next(iterator).decode("utf-8").rstrip())
        except StopIteration:
            pass

        return logs

    def _set_flags(self, pipeline, directives):
        # Set the can_build flag
        self.can_build = (
            hasattr(directives, "BUILD")
            or pipeline.auto_build
        )

        # Set the cache flag to indicate whether kaniko should cache the image
        self.can_cache = pipeline.cache or hasattr(directives, "CACHE")

    def _status_to_text(self, status):
        return "ran successfully" if status == 0 else "failed"

handler = Docker()