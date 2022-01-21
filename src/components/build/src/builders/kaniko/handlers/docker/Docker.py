import json, uuid, time, os

import docker

from conf.configs import SCRATCH_DIR
from core.AbstractBuildHandler import AbstractBuildHandler


class Docker(AbstractBuildHandler):
    def __init__(self):
        self.run_file = None

    def handle(self, build_context):
        # Create a docker client
        client = docker.from_env()

        # Generate bash script
        filename = self.generate_file()

        # Credentials for destination image registry
        # Create the config file in which the credentials will be stored
        self.add_cmd("mkdir -p /kaniko/.docker")

        # Add the credentials json object to the file
        registry_creds = {
            "auths": {
                "nathandf/jscicd-kaniko-test": {
                    "auth": f"{os.environ['REGISTRY_USER']} {os.environ['REGISTRY_TOKEN']}"
                }
            }
        }
        self.add_cmd(f"echo {json.dumps(registry_creds)} > /kaniko/.docker/config.json")

        # Create the directory for the mounted runfile
        self.add_cmd("mkdir -p /cicd/scratch")

        # Build the cmd for kaniko based on the build_context.
        kaniko_cmd = (
            "/kaniko/executor"
            f" --context {build_context.context}"
            f" --dockerfile {build_context.dockerfile_path}"
            f" --destination {build_context.destination}"
                if build_context.destination is not None else f" --no-push"
        )

        # Context arg (the repository in which the Dockerfile lives)
        self.add_cmd(kaniko_cmd)

        print(kaniko_cmd)

        # Run the kaniko build
        container = client.containers.run(
            "gcr.io/kaniko-project/executor:debug",
            f"sh {self.run_file}",
            mounts={self.run_file: {"bind": "/cicd/scratch", "mode": "rw"}},
            detach=True,
            entrypoint=""
        )

        print(container)

        print(container.logs(stderr=True, stdout=True))

        # Remove the container upon completion
        #container.remove()

        # Delete the run_file from the scratch dir
        os.remove(self.run_file)
        print(f"Run file config deleted: {self.run_file}")

    def add_cmd(self, cmd):
        # Write the commands to the docker bash
        with open(self.run_file, "a") as file:
            file.write(cmd + "\n")

    def generate_file(self):
        filename = f"docker-{time.time() * 1000}-{str(uuid.uuid4())}.sh"
        self.run_file = SCRATCH_DIR + filename
        
        with open(self.run_file, "w") as file:
            file.write("#!/bin/sh\n")
        return filename



handler = Docker()