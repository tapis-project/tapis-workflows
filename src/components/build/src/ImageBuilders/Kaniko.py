import json, time, uuid

import yaml

from conf.configs import BASE_KANIKO_FILE, WORK_DIR


class Kaniko:

    def build(self, request):
        # Load a fresh kaniko config from the kaniko template file
        self.load_config()

        # Build the config file with the data of the build request
        # and store it in the work dir
        config_path = self._prepare_config(request)

        print(config_path)

    def add_arg(self, arg, value):
        if value is not None:
            value = "=" +  value
        # Add the argument(and value if it exists) to the args array of the 
        # kaniko config
        self.config["spec"]["template"]["spec"]["containers"][0]["args"].append(f"{arg}{value}")

    def _prepare_config(self, request):
        build_context = json.loads(request)

        # Add the context, docerkfile, and destination(or --no-push) arguments that
        # kaniko requires
        # --context is the git repositry that kaniko pulls for the build
        self.add_arg("--context", build_context["context"])

        # --dockerfile is the path to the Dockerfile in the repository
        self.add_arg("--dockerfile", build_context["dockerfile_path"])

        # --destination is the image registry that the newly built image will be pushed to.
        # If none is specificed, the argument --no-push will be passed to kaniko
        if build_context["destination"] == None:
            self.add_arg("--no-push")
        else:
            self.add_arg("--destination", build_context["destination"])

        # Create a unique filename for the kaniko config
        filename = self._create_config_filename()
        config_path = WORK_DIR + filename

        # Write the arguments to the config
        file = open(config_path, "w")
        yaml.dump(self.config, file)
        file.close()

        return config_path

    def _create_config_filename(self):
        return f"kaniko-{time.time() * 1000}-{str(uuid.uuid4())}.yml"

    def load_config(self):
        self.config = yaml.safe_load(
            open(BASE_KANIKO_FILE, "r").read()
        )


image_builder = Kaniko()