from django.db import DatabaseError, IntegrityError, OperationalError
from django.forms.models import model_to_dict

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.models import ModelResponse, ModelListResponse
from backend.views.http.responses.errors import (
    ServerError,
    Forbidden,
    NotFound,
    BadRequest
)
from backend.services.GroupService import service as group_service
from backend.models import PipelineRun, Pipeline


class PipelineRuns(RestrictedAPIView):
    def get(self, request, group_id, pipeline_id, pipeline_run_uuid=None, *_,  **__):
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

            if pipeline_run_uuid == None:
                return self.list(pipeline)

            run = PipelineRun.objects.filter(
                pipeline=pipeline,
                uuid=pipeline_run_uuid
            ).first()

            if run == None:
                return BadRequest(f"PiplineRun with uuid '{pipeline_run_uuid}' does not exist")

            # Format the started at and last_modified
            run = model_to_dict(run)
            run["started_at"] = run["started_at"].strftime("%Y-%m-%d %H:%M:%S")
            run["last_modified"] = run["last_modified"].strftime("%Y-%m-%d %H:%M:%S")

            return BaseResponse(
                status=200,
                success=True,
                message="success",
                result=run
            )
            
        # TODO catch the specific error thrown by the group service
        except (DatabaseError, IntegrityError, OperationalError) as e:
            return ServerError(message=e.__cause__)
        except Exception as e:
            return ServerError(message=e)


    def list(self, pipeline):
        runs = []
        try:
            run_models = PipelineRun.objects.filter(pipeline=pipeline)
            for run_model in run_models:
                run = model_to_dict(run_model)
                run["started_at"] = run["started_at"].strftime("%Y-%m-%d %H:%M:%S")
                run["last_modified"] = run["last_modified"].strftime("%Y-%m-%d %H:%M:%S")
                runs.append(run)
                
            return BaseResponse(
                status=200,
                success=True,
                message="success",
                result=runs
            )
        except (DatabaseError, IntegrityError, OperationalError) as e:
            return ServerError(message=e.__cause__)
        except Exception as e:
            return ServerError(message=e)

        