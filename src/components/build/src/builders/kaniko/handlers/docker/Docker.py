import json, uuid, time, os, base64

import docker

from core.AbstractBuildHandler import AbstractBuildHandler


class Docker(AbstractBuildHandler):
    def __init__(self):
        self.config_file = None

    def handle(self, deployment):
        print(deployment)
        # Create a docker client
        client = docker.from_env()

        # Generate config script
        self.generate_config(deployment)

        # Build the cmd for kaniko based on the deployment.
        kaniko_cmd = (
            "/kaniko/executor" +
            " --cache=false" +
            f" --context {deployment.context}" +
            (f" --context-sub-path {deployment.context_sub_path}" 
                if deployment.context_sub_path is not None else "") +
            f" --dockerfile {deployment.dockerfile_path}" +
            (f" --destination {deployment.destination}"
                if deployment.destination is not None else f" --no-push") +
            (f" --git branch={deployment.branch}"
                if deployment.branch is not None else "")
        )

        # Run the kaniko build
        container = client.containers.run(
            "gcr.io/kaniko-project/executor:debug",
            volumes={
                self.config_file: {"bind": "/kaniko/.docker/config.json", "mode": "ro"},
                "kaniko-data": {"bind": "/kaniko-data/", "mode": "rw"}
            },
            detach=True,
            entrypoint=kaniko_cmd,
            # auto_remove=True
        ).wait()

        self.reset()

    def generate_config(self, deployment):
        self.config_file = f"/tmp/docker-config-{time.time() * 1000}-{str(uuid.uuid4())}.json"

        # Base64 encode credentials
        encoded_creds = base64.b64encode(
            f"{deployment.registry_secret.key}:{deployment.registry_secret.value}"
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

        print("creds", registry_creds)
        
        print(f"Creating config file: {self.config_file}")

        with open(self.config_file, "w") as file:
            file.write(json.dumps(registry_creds))

    def reset(self):
        # Delete the config file
        os.remove(self.config_file)
        print(f"Config file deleted: {self.config_file}")

        self.config_file = None



handler = Docker()