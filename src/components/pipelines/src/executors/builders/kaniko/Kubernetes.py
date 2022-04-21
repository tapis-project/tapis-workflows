import yaml

from kubernetes import config, client, utils

from conf.configs import BASE_KANIKO_FILE
from core.ActionResult import ActionResult
from core.BaseBuildExecutor import BaseBuildExecutor
from core.resources import FileResource, ConfigMapResource, JobResource


class Kubernetes(BaseBuildExecutor):
    def __init__(self, action, message):
        BaseBuildExecutor.__init__(self, action, message)

        # Load the kubernetes cluster config and initialize the kubernetes api client
        config.load_incluster_config()
        self.api = client.CoreV1Api()

        # Load a fresh kaniko base config
        self.kaniko_config = yaml.safe_load(open(BASE_KANIKO_FILE, "r").read())

    def execute(self, on_finish_callback) -> ActionResult:
        # Create the kaniko job
        job_name = self._create_kaniko_job()

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

        # TODO implement on_finish_callback

        return ActionResult(status=0)

    def _add_arg(self, arg):
        # Add the argument to the args array of the 
        # kaniko config
        self.kaniko_config["spec"]["template"]["spec"]["containers"][0]["args"].append(f"{arg}")

    def _create_kaniko_job(self):
        # Set the name for the k8 job metadata
        job_name = f"{self.group.id}.{self.pipeline.id}.{self.action.id}"

        # Set the name of the job
        self.kaniko_config["metadata"]["name"] = job_name

        # Build the config file with the data of the build request
        # and store it in the scratch dir
        kaniko_config_path = self._create_kaniko_config(job_name)

        # Apply the kaniko config to run the job
        # TODO try block
        utils.create_from_yaml(client.ApiClient(), kaniko_config_path)

        # Register the job to be deleted after execution
        self._register_resource(JobResource(name=job_name))

        return job_name

    def _create_kaniko_config(self, job_name):
        """Add the context, docerkfile, and destination(or --no-push) arguments that
        kaniko requires, create the kaniko config in the scratch dir, and create the
        dockerhub config file that will be mounted into the kaniko job container
        to authenticate with dockerhub"""

        # Enable image layer caching for imporved performance
        can_cache = self.action.cache or hasattr(self.directives, "CACHE")
        self._add_arg(f"--cache={'true' if can_cache else 'false'}")

        # Source of dockerfile for image to be build
        context = self._resolve_context_string()
        self._add_arg(f"--context={context}")

        # Useful when your context is, for example, a git repository,
        #  and you want to build one of its subfolders instead of the root folder
        if self.action.context.sub_path is not None:
            self._add_arg(f"--context-sub-path={self.action.context.sub_path}")

        # The branch to be pulled
        self._add_arg(f"--git=\"branch={self.action.context.branch}\"")

        # path to the Dockerfile in the repository
        self._add_arg(f"--dockerfile={self.action.context.dockerfile_path}")

        # the image registry that the image will be pushed to
        destination = self._resolve_destination_string()
        destination_arg = "--no-push"

        if destination is not None:
            destination_arg = f"--destination={destination}"

        self._add_arg(destination_arg)

        # Mount the credentials kaniko will use to push the image to the desitination
        if destination is not None:
            self._create_dockerhub_config()
            regcred_configmap_name = self._create_regcred_configmap(job_name)

            # Add the mounts for the new configmap to the kaniko config
            self.kaniko_config["spec"]["template"]["spec"]["volumes"][0]["configMap"]["name"] = regcred_configmap_name
                
        # Create a unique filename for the kaniko config
        kaniko_config_path = self.action.scratch_dir + "kaniko.yml"

        # Write the kaniko config to the config file
        file = open(kaniko_config_path, "w")
        yaml.dump(self.kaniko_config, file)
        file.close()

        # Register the kaniko config for cleanup after execution
        self._register_resource(FileResource(path=kaniko_config_path))

        return kaniko_config_path

    def _create_regcred_configmap(self, job_name):
        configmap_name = f"dockerhub.regcred.{job_name}"

        # Setup ConfigMap metadata
        metadata = client.V1ObjectMeta(
            labels=dict(job=job_name),
            name=configmap_name,
            namespace="default",
        )

        # Get the contents of the dockerhub config file
        data = None
        with open(f"{self.dockerhub_config_dir}config.json", "r") as file:
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

        self._register_resource(ConfigMapResource(name=configmap_name))

        return configmap_name
        
