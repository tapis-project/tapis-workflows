import os, logging

from kubernetes import config, client

from core.resources import Resource, ResourceType
from conf.configs import DEFAULT_POLLING_INTERVAL, KUBERNETES_NAMESPACE

class ActionExecutor:
    def __init__(self, action, message):
        self.action = action
        self.pipeline = message.pipeline
        self.group = message.group
        self.event = message.event
        self.directives = message.directives
        self.message = message
        self.polling_interval = DEFAULT_POLLING_INTERVAL
        self._resources: list[Resource] = []

        # Create the base directory for all files and output created during this action execution
        work_dir = f"{self.message.pipeline.work_dir}{action.id}/"
        os.mkdir(work_dir)

        # Create the scratch dir for files created in support of the action execution
        scratch_dir = f"{work_dir}scratch/"
        os.mkdir(scratch_dir)
        self.action.scratch_dir = scratch_dir

        # Create the output dir in which the output of the action execution will be stored
        output_dir = f"{work_dir}output/"
        os.mkdir(output_dir)
        self.action.output_dir = output_dir
        
        # Connect to the kubernetes cluster and instatiate the api instances
        config.load_incluster_config()
        self.core_v1_api = client.CoreV1Api()
        self.batch_v1_api = client.BatchV1Api()

        # Set the polling interval for the action executor based on the
        # the action TTL
        self._set_polling_interval()

    def _set_polling_interval(self):
        # TODO determine polling interval based on TTL
        self.polling_interval = DEFAULT_POLLING_INTERVAL

    def _job_in_terminal_state(self, job):
        return self._job_failed(job) or self._job_succeeded(job)

    def _job_failed(self, job):
        return type(job.status.failed) == int and job.status.failed > 0

    def _job_succeeded(self, job):
        return type(job.status.succeeded) == int and job.status.succeeded > 0

    def _register_resource(self, resource: Resource):
        self._resources.append(resource)

    def _store_result(self, filename, value, flag="wb"):
        with open(f"{self.action.output_dir}{filename.lstrip('/')}", flag) as file:
            file.write(value)

    def cleanup(self):
        logging.debug(f"Total resources to clean: ({len(self._resources)})")
        for resource in self._resources:
            # ConfigMaps
            if resource.type == ResourceType.configmap:
                self.core_v1_api.delete_namespaced_config_map(
                    name=resource.configmap.metadata.name,
                    namespace=KUBERNETES_NAMESPACE
                )
                continue
            
            # Jobs and Job Pods
            if resource.type == ResourceType.job:
                body = client.V1DeleteOptions(propagation_policy="Background")
                self.batch_v1_api.delete_namespaced_job(
                    name=resource.job.metadata.name,
                    namespace=KUBERNETES_NAMESPACE,
                    body=body
                )
                continue