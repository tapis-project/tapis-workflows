import time, uuid, os

import yaml

from conf.configs import BASE_KANIKO_FILE, SCRATCH_DIR
from core.ActionResult import ActionResult
from core.BaseBuildDispatcher import BaseBuildDispatcher

class Kubernetes(BaseBuildDispatcher):
    def dispatch(self, build_context) -> ActionResult:
        # Load a fresh kaniko base config
        self._load_config()

        # Build the config file with the data of the build request
        # and store it in the scratch dir
        config_path = self._prepare_config(build_context)

        print(f"Build start: {config_path}")
        # TODO apply the kaniko config in the scratch dir using the kubernetes api
        print(f"Build end: {config_path}")

        # Delete the config from the scratch dir
        os.remove(config_path)
        print(f"Kaniko config deleted: {config_path}")

        return ActionResult(status=0)

    def _add_arg(self, arg, value):
        if value is not None:
            value = "=" +  value
        # Add the argument(and value if it exists) to the args array of the 
        # kaniko config
        self.config["spec"]["template"]["spec"]["containers"][0]["args"].append(f"{arg}{value}")

    def _prepare_config(self, build_context):

        # Add the context, docerkfile, and destination(or --no-push) arguments that
        # kaniko requires
        # --context is the git repositry that kaniko pulls for the build
        self._add_arg("--context", build_context.context)

        # --dockerfile is the path to the Dockerfile in the repository
        self._add_arg("--dockerfile", build_context.dockerfile_path)

        # --destination is the image registry that the newly built image will be pushed to.
        # If none is specificed, the argument --no-push will be passed to kaniko
        if build_context.destination == None:
            self._add_arg("--no-push")
        else:
            self._add_arg("--destination", build_context.destination)

        # Create a unique filename for the kaniko config
        filename = self._create_config_filename()
        config_path = SCRATCH_DIR + filename
        print(f"Kaniko config created: {config_path}")

        # Write the arguments to the config
        file = open(config_path, "w")
        yaml.dump(self.config, file)
        file.close()

        return config_path

    def _create_config_filename(self):
        return f"kaniko-{time.time() * 1000}-{str(uuid.uuid4())}.yml"

    def _load_config(self):
        self.config = yaml.safe_load(
            open(BASE_KANIKO_FILE, "r").read()
        )

handler = Kubernetes()
        
