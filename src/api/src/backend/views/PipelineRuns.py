from django.db import DatabaseError, IntegrityError, OperationalError
from django.forms.models import model_to_dict

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.errors import (
    ServerError as ServerErrorResp,
    Forbidden,
    NotFound,
    BadRequest
)
from backend.services.GroupService import service as group_service
from backend.models import PipelineRun, Pipeline, TERMINAL_STATUSES
from backend.helpers.PipelineDispatchRequestBuilder import PipelineDispatchRequestBuilder
from backend.services.PipelineDispatcher import service as pipeline_dispatcher
from backend.views.http.responses.models import ModelResponse
from backend.errors.api import ServerError
from backend.utils import logger
from backend.services.CredentialsService import service as credentials_service


request_builder = PipelineDispatchRequestBuilder(credentials_service)

class PipelineRuns(RestrictedAPIView):
    def post(self, request, group_id, pipeline_id, pipeline_run_uuid):
        try:
            # Get the group
            group = group_service.get(group_id, request.tenant_id)
            if group == None:
                return NotFound(f"No group found with id '{group_id}'")

            # Check that the user belongs to the group
            if not group_service.user_in_group(request.username, group_id, request.tenant_id):
                return Forbidden(message="You do not have access to this group")
            
            # Find a pipeline that matches the request data
            pipeline = Pipeline.objects.filter(
                id=pipeline_id,
                group=group
            ).prefetch_related(
                "group",
                "archives",
                "archives__archive",
                "tasks",
                "tasks__context",
                "tasks__context__credentials",
                "tasks__context__identity",
                "tasks__destination",
                "tasks__destination__credentials",
                "tasks__destination__identity",
            ).first()

            # Return if NotFound if no pipeline found
            if pipeline == None:
                return NotFound(f"Pipline '{pipeline_id}' does not exist")

            # Return NotFound if run not found
            pipeline_run = PipelineRun.objects.filter(
                pipeline=pipeline,
                uuid=pipeline_run_uuid
            ).first()
            
            if not pipeline_run:
                return BadRequest(f"PiplineRun with uuid '{pipeline_run_uuid}' does not exist")
            
            if pipeline_run.status in TERMINAL_STATUSES:
                return BadRequest(f"PiplineRun with uuid '{pipeline_run_uuid}' is not in a terminable state")

            try:
                # Build the pipeline dispatch request
                pipeline_dispatch_request = request_builder.build(
                    request.base_url,
                    group,
                    pipeline,
                    directives={"TEMINATE_RUN": [pipeline_run_uuid]},
                    args={},
                    run=pipeline_run,
                )
                # Dispatch the request
                run = pipeline_dispatcher.dispatch(pipeline_dispatch_request, pipeline, pipeline_run=pipeline_run)
            except ServerError as e:
                return ServerErrorResp(message=str(e))
            except Exception as e:
                return ServerErrorResp(message=str(e))

            # Respond with the pipeline run
            return ModelResponse(run)
            
        # TODO catch the specific error thrown by the group service
        except (DatabaseError, IntegrityError, OperationalError) as e:
            logger.exception(e.__cause__)
            return ServerError(message=e.__cause__)
        except Exception as e:
            logger.exception(e.__cause__)
            return ServerError(message=e)

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
            
            run["started_at"] = run["started_at"].strftime("%Y-%m-%d %H:%M:%S") if run["started_at"] else None
            run["last_modified"] = run["last_modified"].strftime("%Y-%m-%d %H:%M:%S") if run["last_modified"] else None

            return BaseResponse(
                status=200,
                success=True,
                message="success",
                result=run
            )
            
        # TODO catch the specific error thrown by the group service
        except (DatabaseError, IntegrityError, OperationalError) as e:
            logger.exception(e.__cause__)
            return ServerError(message=e.__cause__)
        except Exception as e:
            logger.exception(e.__cause__)
            return ServerError(message=e)


    def list(self, pipeline):
        runs = []
        try:
            run_models = PipelineRun.objects.filter(pipeline=pipeline)
            for run_model in run_models:
                run = model_to_dict(run_model)
                
                run["started_at"] = run["started_at"].strftime("%Y-%m-%d %H:%M:%S") if run["started_at"] else None
                run["last_modified"] = run["last_modified"].strftime("%Y-%m-%d %H:%M:%S")  if run["last_modified"] else None
                runs.append(run)

            return BaseResponse(
                status=200,
                success=True,
                message="success",
                result=runs
            )
        except (DatabaseError, IntegrityError, OperationalError) as e:
            logger.exception(e.__cause__)
            return ServerError(message=e.__cause__)
        except Exception as e:
            logger.exception(e.__cause__)
            return ServerError(message=e)

        