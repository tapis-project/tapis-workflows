import os, logging

import docker

from core.ActionResult import ActionResult
from core.BaseBuildExecutor import BaseBuildExecutor
from conf.configs import LOG_FILE


class Docker(BaseBuildExecutor):
    def __init__(self):
        self.dockerhub_config_file = None

    def execute(self, action, message):
        # Resolve the repository from which the code containing the Dockerfile
        # will be pulled
        context = self._resolve_context_string(action)

        # Resolve the image registry to which the image will be pushed after build
        destination = self._resolve_destination_string(
            action, message.event, message.directives
        )

        # Do not build if there is no BUILD directive and
        # the auto_build flag set to False
        if (hasattr(message.directives, "BUILD") or action.auto_build) == False:
            logging.info("Build cancelled. No 'build' directive found.")
            self._reset()
            return

        # Create a docker client
        client = docker.from_env()

        # Generate the credentials config that kaniko will use to push the
        # image to an image registry
        self._create_dockerhub_config(action, message.pipeline)

        # Build the entrypoint for the kaniko executor based on the pipeline
        # and directives
        can_cache = action.cache or hasattr(message.directives, "CACHE")
        entrypoint = (
            "/kaniko/executor"
            + f" --cache={'true' if can_cache else 'false'}"
            + f" --context {context}"
            +
            # f" --force" +
            (
                f" --context-sub-path {action.context.sub_path}"
                if action.context.sub_path is not None
                else ""
            )
            + f" --dockerfile {action.context.dockerfile_path}"
            + (
                f" --destination {destination}"
                if action.destination is not None
                else f" --no-push"
            )
            + (
                f" --git branch={action.context.branch}"
                if action.context.branch is not None
                else ""
            )
        )

        # Run the kaniko build
        container = client.containers.run(
            "gcr.io/kaniko-project/executor:debug",
            volumes={
                self.dockerhub_config_file: {
                    "bind": "/kaniko/.docker/config.json",
                    "mode": "ro",
                }
            },
            detach=True,
            entrypoint=entrypoint,
            stderr=True,
            stdout=True,
            mem_limit="5g",
            memswap_limit="5g",
        )

        # TODO Update the build status to "in_progress"

        logs = []
        for line in container.logs(stream=True):
            line = line.decode("utf8").replace("'", '"')
            logs.append(line)
            file = open(LOG_FILE, "a")
            file.write(line)
            file.close()
            logging.info(line)

        # Remove the container and reset the builder
        container.remove()

        self._reset(delete_config=True)

        return ActionResult(0, data={})
        # return ActionResult(result["StatusCode"], data=result)

    def _reset(self, delete_config=False):
        # Delete the config file
        if delete_config:
            os.remove(self.dockerhub_config_file)

        self.dockerhub_config_file = None

    def _get_container_logs(self, client, container):
        logs = []
        iterator = client.containers.get(container.name).logs(stream=True, follow=False)
        try:
            while True:
                logs.append(next(iterator).decode("utf-8").rstrip())
        except StopIteration:
            pass

        return logs
