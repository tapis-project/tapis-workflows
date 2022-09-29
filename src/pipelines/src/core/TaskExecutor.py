import os, logging

from kubernetes import config, client

from utils import lbuffer_str as lbuf
from core.events import EventPublisher, EventExchange, Event
from core.events.types import TASK_TERMINATED
from core.resources import Resource, ResourceType
from conf.constants import (
    DEFAULT_POLLING_INTERVAL,
    KUBERNETES_NAMESPACE,
)


PSTR = lbuf('[PIPELINE]')
TSTR = lbuf('[TASK]')

class TaskExecutor(EventPublisher):
    def __init__(self, task, ctx, exchange: EventExchange):
        # Enabling task executors to publish events to the exchange. 
        EventPublisher.__init__(self, exchange)

        self.ctx = ctx
        self.task = task
        self.pipeline = self.ctx.pipeline
        self.group = self.ctx.group
        self.event = self.ctx.event
        self.directives = self.ctx.directives
        self.polling_interval = DEFAULT_POLLING_INTERVAL
        self._resources: list[Resource] = []

        # Initialize the file system
        self._initialize_fs()

        # Connect to the kubernetes cluster and instatiate the api instances
        config.load_incluster_config()
        self.core_v1_api = client.CoreV1Api()
        self.batch_v1_api = client.BatchV1Api()

        # Set the polling interval for the task executor based on the
        # the task max_exec_time
        self._set_polling_interval(task)

        print("Sleeping...")
        import time
        time.sleep(5)

    def _set_polling_interval(self, task):
        # Default is already the DEFAULT_POLLING_INTERVAL
        if task.max_exec_time <= 0: return
        
        # TODO Replace line below.
        # Calculate the interval based on the max_exec_time of the task
        interval = self.polling_interval

        self.polling_interval = interval if interval >= 1 else self.polling_interval

    def _job_in_terminal_state(self, job):
        return (self._job_failed(job) or self._job_succeeded(job)) and job.status.active == None

    def _job_failed(self, job):
        return type(job.status.failed) == int and job.status.failed > 0

    def _job_succeeded(self, job):
        return type(job.status.succeeded) == int and job.status.succeeded > 0

    def _register_resource(self, resource: Resource):
        self._resources.append(resource)

    def _store_result(self, filename, value, flag="wb"):
        with open(f"{self.task.output_dir}{filename.lstrip('/')}", flag) as file:
            file.write(value)

    def _initialize_fs(self):
        # Create the base directory for all files and output created during this task execution
        self.task.work_dir = f"{self.pipeline.work_dir}{self.task.id}/"
        os.makedirs(self.task.work_dir, exist_ok=True)

        # Create the scratch dir for files created in support of the task execution
        self.task.scratch_dir = f"{self.task.work_dir}scratch/"
        os.makedirs(self.task.scratch_dir, exist_ok=True)

        # Create the output dir in which the output of the task execution will be stored
        self.task.output_dir = f"{self.task.work_dir}output/"
        os.makedirs(self.task.output_dir, exist_ok=True)        

    def cleanup(self):
        logging.info(f"{TSTR} {self.task.id} [CLEANUP STARTED]")

        for resource in self._resources:
            # ConfigMaps
            if resource.type == ResourceType.configmap:
                self.core_v1_api.delete_namespaced_config_map(
                    name=resource.configmap.metadata.name,
                    namespace=KUBERNETES_NAMESPACE,
                )
                continue

            # Jobs and Job Pods
            if resource.type == ResourceType.job:
                body = client.V1DeleteOptions(propagation_policy="Background")
                self.batch_v1_api.delete_namespaced_job(
                    name=resource.job.metadata.name,
                    namespace=KUBERNETES_NAMESPACE,
                    body=body,
                )
                continue

        logging.info(f"{TSTR} {self.task.id} [CLEANUP COMPLETED]")

    def terminate(self):
        self.publish(Event(TASK_TERMINATED, self.ctx))
        logging.info(f"{TSTR} {self.task.id} [TERMINATING] {self.__class__.__name__}")
        self.cleanup()
        logging.info(f"{TSTR} {self.task.id} [TERMINATING] {self.__class__.__name__}")

