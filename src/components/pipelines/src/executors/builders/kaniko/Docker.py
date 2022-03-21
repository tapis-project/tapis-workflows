import json, uuid, time, os, base64

import docker

from core.ActionResult import ActionResult
from core.BaseBuildExecutor import BaseBuildExecutor
from errors.credential import CredentialError
from conf.configs import LOG_FILE


class Docker(BaseBuildExecutor):
    def __init__(self):
        self.config_file = None

    def execute(self, action, message):
        # Resolve the repository from which the code containing the Dockerfile
        # will be pulled
        context = self._resolve_context_string(action)
        
        # Resolve the image registry to which the image will be pushed after build
        destination = self._resolve_destination_string(
            action, message.event, message.directives)

        # Do not build if there is no BUILD directive and
        # the auto_build flag set to False
        if (hasattr(message.directives, "BUILD") or action.auto_build) == False:
            print("Build cancelled. No 'build' directive found.")
            self._reset()
            return
        
        # Create a docker client
        client = docker.from_env()

        # Generate the credentials config that kaniko will use to push the
        # image to an image registry
        self._generate_config(action)

        # Build the entrypoint for the kaniko executor based on the pipeline
        # and directives
        can_cache = action.cache or hasattr(message.directives, "CACHE")
        entrypoint = (
            "/kaniko/executor" +
            f" --cache={'true' if can_cache else 'false'}" +
            f" --context {context}" +
            f" --force" +
            (f" --context-sub-path {action.context.sub_path}"
                if action.context.sub_path is not None else "") +
            f" --dockerfile {action.context.dockerfile_path}" +
            (f" --destination {destination}"
                if action.destination is not None else f" --no-push") +
            (f" --git branch={action.context.branch}"
                if action.context.branch is not None else "")
        )

        # Run the kaniko build
        container = client.containers.run(
            "gcr.io/kaniko-project/executor:debug",
            volumes={
                self.config_file: {"bind": "/kaniko/.docker/config.json", "mode": "ro"}
            },
            detach=True,
            entrypoint=entrypoint,
            stderr=True,
            stdout=True,
        )

        # TODO Update the build status to "in_progress"

        logs = []
        for line in container.logs(stream=True):
            line = line.decode('utf8').replace("'", '"')
            logs.append(line)
            file = open(LOG_FILE, "a")
            file.write(line)
            file.close()
            print(line)


        # Remove the container and reset the builder
        # container.remove()

        self._reset(delete_config=True)
        
        return ActionResult(0, data={})
        # return ActionResult(result["StatusCode"], data=result)
 
    def _generate_config(self, action):
        # Get image registry credentials from config
        credential = action.destination.credential

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

    def _reset(self, delete_config=False):
        # Delete the config file
        if delete_config:
            os.remove(self.config_file)

        self.config_file = None

    def _get_container_logs(self, client, container):
        logs = []
        iterator = client.containers.get(container.name).logs(stream=True, follow=False)
        try:
            while True:
                logs.append(next(iterator).decode("utf-8").rstrip())
        except StopIteration:
            pass

        return logs