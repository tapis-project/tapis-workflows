import uuid, json

import yaml

from kubernetes import config, client, utils

from conf.configs import BASE_KANIKO_FILE, SCRATCH_DIR
from core.ActionResult import ActionResult
from core.BaseBuildExecutor import BaseBuildExecutor

class Kubernetes(BaseBuildExecutor):
    def __init__(self):
        config.load_incluster_config()
        self.api = client.CoreV1Api()

    def execute(self, action, message) -> ActionResult:
        # Load a fresh kaniko base config
        self.kaniko_config = yaml.safe_load(open(BASE_KANIKO_FILE, "r").read())

        # Set the name for the k8 job metadata
        job_name = f"{message.pipeline.id}.{action.id}"
        self.kaniko_config["metadata"]["name"] = job_name

        # Build the config file with the data of the build request
        # and store it in the scratch dir
        kaniko_config_path = self._create_kaniko_config(job_name, action, message)

        print("Kaniko config: ", self.kaniko_config)

        # Apply the kaniko config to run the job
        utils.create_from_yaml(client.ApiClient(), kaniko_config_path)

        try:
            pod_log_response = self.api.read_namespaced_pod_log(
                name=job_name,
                namespace="default",
                _return_http_data_only=True,
                _preload_content=False
            
            )
            pod_log = pod_log_response.data.decode("utf-8")
            print(pod_log)
        except Exception as e:
            print("Pipelines Error: ", e)

        # Delete the config from the scratch dir
        # os.remove(kaniko_config_path)
        # print(f"Kaniko config deleted: {kaniko_config_path}")

        return ActionResult(status=0)

    def _add_arg(self, arg):
        # Add the argument to the args array of the 
        # kaniko config
        self.kaniko_config["spec"]["template"]["spec"]["containers"][0]["args"].append(f"{arg}")

    def _create_kaniko_config(self, job_name, action, message):
        """Add the context, docerkfile, and destination(or --no-push) arguments that
        kaniko requires, create the kaniko config in the scratch dir, and create the
        dockerhub config file that will be mounted into the kaniko job container
        to authenticate with dockerhub"""

        # Enable image layer caching for imporved performance
        can_cache = action.cache or hasattr(message.directives, "CACHE")
        self._add_arg(f"--cache={'true' if can_cache else 'false'}")

        # Source of dockerfile for image to be build
        context = self._resolve_context_string(action)
        self._add_arg(f"--context={context}")

        # Useful when your context is, for example, a git repository,
        #  and you want to build one of its subfolders instead of the root folder
        if action.context.sub_path is not None:
            self._add_arg(f"--context-sub-path={action.context.sub_path}")

        # The branch to be pulled
        self._add_arg(f"--git=\"branch={action.context.branch}\"")

        # path to the Dockerfile in the repository
        self._add_arg(f"--dockerfile={action.context.dockerfile_path}")

        # the image registry that the image will be pushed to
        destination = self._resolve_destination_string(action, message.event, message.directives)
        destination_arg = "--no-push"

        if destination is not None:
            destination_arg = f"--destination={destination}"

        self._add_arg(destination_arg)

        # Mount the credentials kaniko will use to push the image to the desitination
        if destination is not None:
            self._create_dockerhub_config(action, message.pipeline)
            self._create_regcred_configmap(job_name, action, message.pipeline)

            # Add the mounts for the new configmap to the kaniko config
            self.kaniko_config["spec"]["template"]["spec"]["volumes"][0]["configMap"]["name"] = \
                f"regcred.{message.pipeline.id}.{action.id}"

        # Create a unique filename for the kaniko config
        filename = self._create_kaniko_config_filename(action, message.pipeline)
        kaniko_config_path = SCRATCH_DIR + filename

        print("Kaniko Config:", self.kaniko_config)

        # Write the kaniko config to the config file
        file = open(kaniko_config_path, "w")
        yaml.dump(self.kaniko_config, file)
        file.close()

        print(f"Kaniko config created: {kaniko_config_path}")

        return kaniko_config_path

    def _create_kaniko_config_filename(self, action, pipeline):
        return f"kaniko-{pipeline.id}-{action.id}-{str(uuid.uuid4())}.yml"

    def _create_regcred_configmap(self, job_name, action, pipeline):
        # Setup ConfigMap metadata
        metadata = client.V1ObjectMeta(
            labels=dict(job=job_name),
            name=f"regcred.{job_name}",
            namespace="default",
        )

        # Get the contents of the dockerhub config file
        data = None
        with open(f"{self.dockerhub_config_dir}/config.json", "r") as file:
            data = file.read()

        # Instantiate the configmap object
        configmap = client.V1ConfigMap( 
            api_version="v1",
            kind="ConfigMap",
            data={"config.json": data},
            metadata=metadata
        )

        self.api.create_namespaced_config_map(
            namespace="default",
            body=configmap
        )
        


handler = Kubernetes()
        
