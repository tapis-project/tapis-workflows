import os

from kubernetes import config, client

from owe_python_sdk.events.types import TASK_TERMINATED
from owe_python_sdk.events import EventPublisher, EventExchange, Event
from owe_python_sdk.TaskResult import TaskResult
from utils import lbuffer_str as lbuf
from core.resources import Resource, ResourceType
from conf.constants import (
    DEFAULT_POLLING_INTERVAL,
    KUBERNETES_NAMESPACE,
)


TSTR = lbuf('[TASK]')

class TaskExecutor(EventPublisher):
    def __init__(self, task, ctx, exchange: EventExchange, plugins=[]):
        # Enabling task executors to publish events to the exchange. 
        EventPublisher.__init__(self, exchange)
        
        self.plugins = plugins
        self.ctx = ctx
        self.task = task
        self.pipeline = self.ctx.pipeline
        self.group = self.ctx.group
        self.event = self.ctx.meta.event
        self.directives = self.ctx.directives
        self.polling_interval = DEFAULT_POLLING_INTERVAL
        self._resources: list[Resource] = []
        self.terminating = False
        self.logger = self.ctx.logger

        # Connect to the kubernetes cluster and instatiate the api instances
        config.load_incluster_config()
        self.core_v1_api = client.CoreV1Api()
        self.batch_v1_api = client.BatchV1Api()

        # Set the polling interval for the task executor based on the
        # the task max_exec_time
        self._set_polling_interval(task)

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

    def _set_output(self, filename, value, flag="wb"):
        with open(f"{self.task.output_dir}{filename.lstrip('/')}", flag) as file:
            file.write(value)

    def _stdout(self, value, flag="wb"):
        self._set_output(".stdout", value, flag=flag)

    def _stderr(self, value, flag="wb"):
        self._set_output(".stderr", value, flag=flag)

    def _get_task_output_files(self):
        return os.listdir(self.task.output_dir)
    
    def _task_result(self, code: int, errors=[], cls=File):
        files = self._get_task_output_files()
        return TaskResult(code, errors=errors, output={self.task.id: files})

    def cleanup(self, terminating=False):
        if terminating: 
            self.logger.info(f"{TSTR} {self.ctx.idempotency_key} {self.task.id} [TERMINATING] {self.__class__.__name__}")
        
        # TODO user server logger below
        #self.logger.info(f"{TSTR} {self.ctx.idempotency_key} {self.task.id} [TASK EXECUTOR CLEANUP]")

        for resource in self._resources:
            # Jobs and Job Pods
            if resource.type == ResourceType.job:
                self.batch_v1_api.delete_namespaced_job(
                    name=resource.job.metadata.name,
                    namespace=KUBERNETES_NAMESPACE,
                    body=client.V1DeleteOptions(propagation_policy="Background"),
                )
                continue

            # ConfigMaps
            if resource.type == ResourceType.configmap:
                self.core_v1_api.delete_namespaced_config_map(
                    name=resource.configmap.metadata.name,
                    namespace=KUBERNETES_NAMESPACE,
                )
                continue

        if terminating:
            self.logger.info(f"{TSTR} {self.ctx.idempotency_key} {self.task.id} [TERMINATED] {self.__class__.__name__}")

    def terminate(self):
        self.terminating = True
        self.publish(Event(TASK_TERMINATED, self.ctx))

