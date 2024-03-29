from django.db import DatabaseError, IntegrityError, OperationalError
from django.forms.models import model_to_dict


from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.responses.BaseResponse import BaseResponse

from backend.views.http.responses.errors import (
    ServerError,
    Forbidden,
    NotFound,
    BadRequest
)
from backend.services.GroupService import service as group_service
from backend.models import Pipeline, PipelineRun, TaskExecution, Task


class TaskExecutions(RestrictedAPIView):
    def get(self, request, group_id, pipeline_id, pipeline_run_uuid, task_execution_uuid=None, *_,  **__):
        try:
            # Get the group
            group = group_service.get(group_id, request.tenant_id)
            if group == None:
                return NotFound(f"No group found with id '{group_id}'")

            # Check that the user belongs to the group
            if not group_service.user_in_group(request.username, group_id, request.tenant_id):
                return Forbidden(message="You do not have access to this group")

            # Get the pipline
            pipeline = Pipeline.objects.filter(
                group=group,
                id=pipeline_id
            ).first()

            # Return if BadRequest if no pipeline found
            if pipeline == None:
                return BadRequest(f"Pipline '{pipeline_id}' does not exist")

            run = PipelineRun.objects.filter(
                pipeline=pipeline,
                uuid=pipeline_run_uuid
            ).first()

            # Return if BadRequest if no pipelinerun found
            if run == None:
                return BadRequest(f"PiplineRun with uuid '{pipeline_run_uuid}' does not exist")

            if task_execution_uuid == None:
                return self.list(run)

            execution_model = TaskExecution.objects.filter(
                uuid=task_execution_uuid
            ).first()

            if execution_model == None:
                return NotFound()

            # Convert the model to a dict and set the task id
            task_id = execution_model.task.id
            execution = model_to_dict(execution_model)
            execution["task_id"] = task_id

            return BaseResponse(
                status=200,
                success=True,
                message="success",
                result=execution
            )

        # TODO catch the specific error thrown by the group service
        except (DatabaseError, IntegrityError, OperationalError) as e:
            return ServerError(message=e.__cause__)
        except Exception as e:
            return ServerError(message=e)

    def list(self, run):
        try:
            execution_models = TaskExecution.objects.filter(pipeline_run=run).prefetch_related("task")
            executions = []
            for execution_model in execution_models:
                # Convert the model to a dict and set the task id
                task_id = execution_model.task.id
                execution = model_to_dict(execution_model)
                execution["task_id"] = task_id

                executions.append(execution)

            return BaseResponse(
                status=200,
                success=True,
                message="success",
                result=executions
            )
        except (DatabaseError, IntegrityError, OperationalError) as e:
            return ServerError(message=e.__cause__)
        except Exception as e:
            return ServerError(message=e)