import json, time, uuid

import yaml

from conf.configs import BASE_KANIKO_FILE, WORK_DIR


class Kaniko:

    def build(self, request):
        self.load_config()
        config_path = self._prepare_config(request)
        print(config_path)

    def add_arg(self, arg, value):
        if value is not None:
            value = "=" +  value
        self.config["spec"]["template"]["spec"]["containers"][0]["args"].append(f"{arg}{value}")

    def _prepare_config(self, request):
        build_context = json.loads(request)

        # Add the context, docerkfile, and destination(or --no-push) arguments that
        # kaniko requires
        self.add_arg("--context", build_context["context"])
        self.add_arg("--dockerfile", build_context["dockerfile_path"])
        if build_context["destination"] == None:
            self.add_arg("--no-push")
        else:
            self.add_arg("--destination", build_context["destination"])

        filename = self._create_config_filename()
        config_path = WORK_DIR + filename

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