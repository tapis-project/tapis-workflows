import docker

from core.AbstractBuildHandler import AbstractBuildHandler


class Docker(AbstractBuildHandler):
    def handle(self, build_context):
        # Create a docker client
        client = docker.from_env()

        # Determine the destination arg for kaniko based on the build_context's
        # destination property
        destination_arg = f"--destination {build_context.destination}"
        if build_context.destination is None:
            destination_arg = "--no-push"

        # commands = [f"""/kaniko/executor \\
        #         --context "{build_context.context}" \\
        #         --dockerfile "{build_context.dockerfile_path}" \\
        #         {destination_arg}
        # """]

        commands = ["echo Test"]

        # Run the kaniko build
        client.containers.run(
            "alpine",
            "echo hello world",
            detach=True,
            #entrypoint=""
        )

        print("worked i guess")


handler = Docker()