from helpers.TapisServiceAPIGateway import TapisServiceAPIGateway

from core.events import Event, EventHandler
from core.events.types import (
    PIPELINE_ACTIVE, PIPELINE_ARCHIVING, PIPELINE_COMPLETED, PIPELINE_FAILED,
    PIPELINE_PENDING, PIPELINE_SUSPENDED, PIPELINE_TERMINATED, PIPELINE_SKIPPED, 
    TASK_ACTIVE, TASK_ARCHIVING, TASK_BACKOFF, TASK_COMPLETED, TASK_FAILED, 
    TASK_PENDING, TASK_SUSPENDED, TASK_TERMINATED, TASK_SKIPPED
)


class TapisWorkflowsAPIBackend(EventHandler):
    def __init__(self, ctx):
        # Set the access token
        access_token = getattr(
            ctx.middleware.backends.tapisworkflowsapi, "access_token", None)

        # Access token is required. If its missing, raise an exception
        if access_token == None:
            raise Exception("Workflow Executor Token missing in request")

        # self._headers = {
        #     "_x_tapis_tenant": ctx.group.tenant_id,
        #     "_x_tapis_user": ctx.pipeline.owner,
        #     # "headers": {
        #     #     "X-WORKFLOW-EXECUTOR-TOKEN": access_token,
        #     #     "X-Tapis-Tenant": ctx.group.tenant_id,
        #     #     "X-Tapis-User": ctx.pipeline.owner
        #     # }
        # }

        # Create a mapping of functions to events
        self.handle_fn_mapping = {
            PIPELINE_ACTIVE:     self._pipeline_active,
            PIPELINE_ARCHIVING:  self._pipeline_archiving,
            PIPELINE_COMPLETED:  self._pipeline_completed,
            PIPELINE_FAILED:     self._pipeline_failed,
            PIPELINE_PENDING:    self._pipeline_pending,
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
            "_tapis_headers": {
                "X-WORKFLOW-EXECUTOR-TOKEN": access_token,
                "X-Tapis-Tenant": ctx.group.tenant_id,
                "X-Tapis-User": ctx.pipeline.owner
            }
        }

        # self._headers={
        #     "X-Tapis-Tenant": ctx.group.tenant_id,
        #     "X-Tapis-User": ctx.pipeline.owner,
        #     "X-Tapis-Token": self.service_client.service_tokens["admin"]["access_token"].access_token
        # }

    def handle(self, event: Event):
        try:
            self.handle_fn_mapping[event.type](event)
        except Exception as e:
            raise e

    def _pipeline_active(self, event):
        self.service_client.workflows.updatePipelineRunStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            status="active",
            **self._kwargs
        )
        print("AFTER ACTIVE")

        

    def _pipeline_completed(self, event):
        self.service_client.workflows.updatePipelineRunStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            status="completed",
            **self._kwargs
        )

    def _pipeline_terminated(self, event):
        self.service_client.workflows.updatePipelineRunStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            status="terminated",
            **self._kwargs
        )

    def _pipeline_archiving(self, event):
        print(f"BACKEND: PIPELINE_ARCHIVING: NOT IMPLEMENTED")

    def _pipeline_failed(self, event):
        self.service_client.workflows.updatePipelineRunStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            status="failed",
            **self._kwargs
        )

    def _pipeline_pending(self, event):
        self.service_client.workflows.updatePipelineRunStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            status="pending",
            **self._kwargs
        )

    def _pipeline_suspended(self, event):
        self.service_client.workflows.updatePipelineRunStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            status="suspended",
            **self._kwargs
        )

    # def _pipeline_skipped(self, event):
    #     self.service_client.workflows.updatePipelineRunStatus(
    #         pipeline_run_uuid=event.payload.pipeline_run.uuid,
    #         status="skipped",
    #         **self._kwargs
    #     )

    def _task_active(self, event, task=None):
        self.service_client.workflows.updateTaskExecutionStatus(
            pipeline_run_uuid=event.payload.pipeline_run.uuid,
            task_id=task.id,
            uuid=task.uuid,
            **self._kwargs
        )

    def _task_archiving(self, event, task=None):
        print(f"BACKEND: TASK_ARCHIVING: NOT IMPLEMENTED")

    def _task_backoff(self, event, task=None):
        print(f"BACKEND: TASK_BACKOFF: NOT IMPLEMENTED")

    def _task_completed(self, event, task=None):
        self.service_client.workflows.updateTaskExecutionStatus(
            task_execution_uuid=task.uuid,
            status="completed",
            **self._kwargs
        )

    def _task_failed(self, event, task=None):
        self.service_client.workflows.updateTaskExecutionStatus(
            task_execution_uuid=task.uuid,
            status="failed",
            **self._kwargs
        )

    def _task_suspended(self, event, task=None):
        self.service_client.workflows.updateTaskExecutionStatus(
            task_execution_uuid=task.uuid,
            status="suspended",
            **self._kwargs
        )
    
    # def _task_skipped(self, event, task=None):
    #     self.service_client.workflows.updateTaskExecutionStatus(
    #         task_execution_uuid=task.uuid,
    #         status="skipped",
    #         **self._kwargs
    #     )

    def _task_terminated(self, event, task=None):
        self.service_client.workflows.updateTaskExecutionStatus(
            task_execution_uuid=task.uuid,
            status="terminated",
            **self._kwargs
        )

    def _task_pending(self, event, task=None):
        self.service_client.workflows.updateTaskExecutionStatus(
            task_execution_uuid=task.uuid,
            status="pending",
            **self._kwargs
        )
    