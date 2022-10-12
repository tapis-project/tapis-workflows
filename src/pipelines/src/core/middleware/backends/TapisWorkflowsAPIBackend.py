from helpers.TapisServiceAPIGateway import TapisServiceAPIGateway

from core.events import Event, EventHandler
from core.events.types import (
    PIPELINE_ACTIVE, PIPELINE_ARCHIVING, PIPELINE_COMPLETED, PIPELINE_FAILED,
    PIPELINE_PENDING, PIPELINE_SUSPENDED, PIPELINE_TERMINATED, TASK_ACTIVE,
    TASK_ARCHIVING, TASK_BACKOFF, TASK_COMPLETED, TASK_FAILED, TASK_PENDING,
    TASK_SUSPENDED, TASK_TERMINATED
)


class TapisWorkflowsAPIBackend(EventHandler):
    def __init__(self, ctx):
        self.ctx = ctx

        # Set the access token
        self.access_token = getattr(
            self.ctx.middleware.backends.tapisworkflowsapi, "access_token", None)

        # Access token is required. If its missing, raise an exception
        if self.access_token == None:
            raise Exception("Workflow Executor Token missing in request")

        # Create a mapping of functions to events
        self.handle_fn_mapping = {
            PIPELINE_ACTIVE:     self._pipeline_active,
            PIPELINE_ARCHIVING:  self._pipeline_archiving,
            PIPELINE_COMPLETED:  self._pipeline_completed,
            PIPELINE_FAILED:     self._pipeline_failed,
            PIPELINE_PENDING:    self._pipeline_pending,
            PIPELINE_SUSPENDED:  self._pipeline_suspended,
            PIPELINE_TERMINATED: self._pipeline_terminated,
            TASK_ACTIVE:         self._task_active,
            TASK_ARCHIVING:      self._task_archiving,
            TASK_BACKOFF:        self._task_backoff,
            TASK_COMPLETED:      self._task_completed,
            TASK_FAILED:         self._task_failed,
            TASK_PENDING:        self._task_pending,
            TASK_SUSPENDED:      self._task_suspended,
            TASK_TERMINATED:     self._task_terminated
        }

    def handle(self, event: Event):
        self.handle_fn_mapping[event.type](event)

    def _pipeline_active(self, event):
        print("BACKEND: PIPELINE ACTIVE")

    def _pipeline_completed(self, event):
        print("BACKEND: PIPELINE COMPLETED")

    def _pipeline_terminated(self, event):
        print(f"BACKEND: PIPELINE TERMINATED: {event.payload.id}")

    def _pipeline_archiving(self, event):
        print("BACKEND: PIPELINE ARCHVING")

    def _pipeline_failed(self, event):
        print("BACKEND: PIPELINE FAILED")

    def _pipeline_pending(self, event):
        print("BACKEND: PIPELINE PENDING")

    def _pipeline_suspended(self, event):
        print("BACKEND: PIPELINE SUSPENDED")

    def _task_active(self, event):
        print(f"BACKEND: TASK: ACTIVE")

    def _task_archiving(self, event):
        print(f"BACKEND: TASK: ARCHIVING")

    def _task_backoff(self, event):
        print(f"BACKEND: TASK: BACKOFF")

    def _task_completed(self, event):
        print(f"BACKEND: TASK: COMPLETED")

    def _task_failed(self, event):
        print(f"BACKEND: TASK: FAILED")

    def _task_suspended(self, event):
        print(f"BACKEND: TASK: SUSPENDED")

    def _task_terminated(self, event):
        print(f"BACKEND: TASK: TERMINATED")

    def _task_pending(self, event):
        print(f"BACKEND: TASK: PENDING")
    