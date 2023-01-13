from django.db import DatabaseError, IntegrityError, OperationalError
from django.utils import timezone

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import TaskExecution as ReqTaskExecution
from backend.views.http.responses import ResourceURLResponse
from backend.views.http.responses.errors import (
    ServerError,
    BadRequest
)
from backend.models import Pipeline, Task, PipelineRun, TaskExecution
from backend.helpers import resource_url_builder
from backend.utils import executor_request_is_valid


class CreateTaskExecution(RestrictedAPIView):
    def post(self, request, pipeline_run_uuid, *_,  **__):
        if not executor_request_is_valid(request):
            return BadRequest(message=f"X-WORKFLOW-EXECUTOR-TOKEN header is invalid")

        prepared_request = self.prepare(ReqTaskExecution)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body
        
        try:
            # Get the pipeline run this task execution belongs to
            run = PipelineRun.objects.filter(uuid=pipeline_run_uuid).first()
            if run == None: return BadRequest(message=f"Pipeline run with uuid {pipeline_run_uuid} not found")
            
            # Get the pipeline
            pipeline = Pipeline.objects.filter(uuid=run.pipeline.uuid).first()
            if pipeline == None: return BadRequest(message=f"Pipeline with uuid {run.pipeline} not found") 

            # Get the task
            task = Task.objects.filter(pipeline=pipeline, id=body.task_id).first()
            if task == None: return BadRequest(message=f"Task with id {body.task_id} not found")

            # Create the task execution
            now = timezone.now()
            TaskExecution.objects.create(
                task=task,
                pipeline_run=run,
                started_at=body.started_at or now,
                last_modified=body.last_modified or now,
                uuid=body.uuid
            )

        except (DatabaseError, IntegrityError, OperationalError) as e:
            return ServerError(message=f"There was an error creating the Task Execution: {e.__cause__}")
        
        return ResourceURLResponse(
            url=resource_url_builder(
                request.url.replace(
                    f"executor/runs/{pipeline_run_uuid}/executions",
                    f"groups/{pipeline.group}/pipelines/{pipeline.id}/runs/{run.uuid}/executions"
                ),
                body.uuid
            )
        )