import os
from threading import Thread

from contrib.tapis.helpers import TapisServiceAPIGateway

from owe_python_sdk.events import Event, EventHandler
from owe_python_sdk.events.types import (
    PIPELINE_ACTIVE, PIPELINE_ARCHIVING, PIPELINE_COMPLETED, PIPELINE_FAILED,
    PIPELINE_PENDING, PIPELINE_SUSPENDED, PIPELINE_TERMINATED, PIPELINE_SKIPPED, 
    TASK_ACTIVE, TASK_ARCHIVING, TASK_BACKOFF, TASK_COMPLETED, TASK_FAILED, 
    TASK_PENDING, TASK_SUSPENDED, TASK_TERMINATED, TASK_SKIPPED
)


class TapisWorkflowsAPIBackend(EventHandler):
    def __init__(self, ctx):
        # Create a mapping of functions to events
        self.handle_fn_mapping = {
            PIPELINE_PENDING:    self._pipeline_pending,
            PIPELINE_ACTIVE:     self._pipeline_active,
            PIPELINE_ARCHIVING:  self._pipeline_archiving,
            PIPELINE_COMPLETED:  self._pipeline_completed,
            PIPELINE_FAILED:     self._pipeline_failed,
            PIPELINE_SUSPENDED:  self._pipeline_suspended,
            PIPELINE_TERMINATED: self._pipeline_terminated,
            # PIPELINE_SKIPPED:    self._pipeline_skipped,
            TASK_ACTIVE:         self._task_active,
            TASK_ARCHIVING:      self._task_archiving,
            TASK_BACKOFF:        self._task_backoff,
            TASK_COMPLETED:      self._task_completed,
            TASK_FAILED:         self._task_failed,
            TASK_PENDING:        self._task_pending,
            TASK_SUSPENDED:      self._task_suspended,
            TASK_TERMINATED:     self._task_terminated,
            # TASK_SKIPPED:        self._task_skipped
        }

        service_api_gateway = TapisServiceAPIGateway()
        self.service_client = service_api_gateway.get_client()

        self._kwargs = {
            "_tapis_set_x_headers_from_service": True,
            "_x_tapis_tenant": ctx.params["tapis_tenant_id"].value,
            "_x_tapis_user": ctx.params["tapis_pipeline_owner"].value,
            "_tapis_headers": {
                "X-WORKFLOW-EXECUTOR-TOKEN": ctx.params["workflow_executor_access_token"].value
            }
        }

    def handle(self, event: Event):
        self.handle_fn_mapping[event.type](event)
        

    def _pipeline_active(self, event):
        self.service_client.workflows.updatePipelineRunStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            status="active",
            logs=self._get_logs(event.payload.pipeline.log_file),
            **self._kwargs
        )
        
        threads = []
        for task in event.payload.pipeline.tasks:
            thread = Thread(
                target=self._create_task_execution,
                args=(event.payload.pipeline_run.uuid, task)
            )
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    def _pipeline_completed(self, event):
        self.service_client.workflows.updatePipelineRunStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            status="completed",
            logs=self._get_logs(event.payload.pipeline.log_file),
            **self._kwargs
        )

    def _pipeline_terminated(self, event):
        self.service_client.workflows.updatePipelineRunStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            status="terminated",
            logs=self._get_logs(event.payload.pipeline.log_file),
            **self._kwargs
        )

    def _pipeline_archiving(self, event):
        print(f"BACKEND: PIPELINE_ARCHIVING: NOT IMPLEMENTED")

    def _pipeline_failed(self, event):
        self.service_client.workflows.updatePipelineRunStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            status="failed",
            logs=self._get_logs(event.payload.pipeline.log_file),
            **self._kwargs
        )

    def _pipeline_pending(self, event):
        self.service_client.workflows.updatePipelineRunStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            status="pending",
            logs=self._get_logs(event.payload.pipeline.log_file),
            **self._kwargs
        )

    def _pipeline_suspended(self, event):
        self.service_client.workflows.updatePipelineRunStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            status="suspended",
            logs=self._get_logs(event.payload.pipeline.log_file),
            **self._kwargs
        )

    # def _pipeline_skipped(self, event):
    #     self.service_client.workflows.updatePipelineRunStatus(
    #         pipeline_run_uuid=event.payload.pipeline_run.uuid,
    #         status="skipped",
    #         **self._kwargs
    #     )

    def _task_active(self, event):
        self.service_client.workflows.updateTaskExecutionStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            task_execution_uuid=event.task.execution_uuid,
            status="active",
            last_message="Task is Active",
            **self._kwargs
        )

    def _task_archiving(self, event):
        print(f"BACKEND: TASK_ARCHIVING: NOT IMPLEMENTED")

    def _task_backoff(self, event):
        print(f"BACKEND: TASK_BACKOFF: NOT IMPLEMENTED")

    def _task_completed(self, event):
        self.service_client.workflows.updateTaskExecutionStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            task_execution_uuid=event.task.execution_uuid,
            status="completed",
            last_message="Task Completed Successfully",
            stdout=self._tail_stdout(event.task),
            stderr=self._tail_stderr(event.task),
            **self._kwargs
        )

    def _task_failed(self, event):
        self.service_client.workflows.updateTaskExecutionStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            task_execution_uuid=event.task.execution_uuid,
            status="failed",
            last_message="Task Failed: " + str(event.result.errors),
            stdout=self._tail_stdout(event.task),
            stderr=self._tail_stderr(event.task),
            **self._kwargs
        )

    def _task_suspended(self, event):
        self.service_client.workflows.updateTaskExecutionStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            task_execution_uuid=event.task.execution_uuid,
            status="suspended",
            last_message="Task Execution has been suspended",
            stdout=self._tail_stdout(event.task),
            stderr=self._tail_stderr(event.task),
            **self._kwargs
        )
    
    # def _task_skipped(self, event):
    #     self.service_client.workflows.updateTaskExecutionStatus(
    #         pipeline_run_uuid=event.payload.pipeline_run.uuid,
    #         task_execution_uuid=event.task.execution_uuid,
    #         status="skipped",
    #         **self._kwargs
    #     )

    def _task_terminated(self, event):
        self.service_client.workflows.updateTaskExecutionStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            task_execution_uuid=event.task.execution_uuid,
            status="terminated",
            last_message="Task Execution has been terminated",
            stdout=self._tail_stdout(event.task),
            stderr=self._tail_stderr(event.task),
            **self._kwargs
        )

    def _task_pending(self, event):
        self.service_client.workflows.updateTaskExecutionStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            task_execution_uuid=event.task.execution_uuid,
            status="pending",
            last_message="Task waiting to be executed",
            **self._kwargs
        )
    
    def _get_logs(self, log_file_path):
        with open(log_file_path, "r") as file:
            return file.read()
        
    def _create_task_execution(self, pipeline_run_uuid, task):
        self.service_client.workflows.createTaskExecution(
            pipeline_run_uuid=pipeline_run_uuid,
            task_id=task.id,
            uuid=task.execution_uuid,
            **self._kwargs
        )

    def _tail_output(self, task, filename, flag="rb", max_bytes=5120):
        with open(f"{task.output_dir}{filename.lstrip('/')}", flag) as file:
            file.seek(max_bytes * -1, os.SEEK_END)
            return file.read()
        
    def _tail_stdout(self, task):
        return self._tail_output(task, ".stdout")
    
    def _tail_stderr(self, task):
        return self._tail_output(task, ".stderr")