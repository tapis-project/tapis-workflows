from django.db import DatabaseError, IntegrityError, OperationalError

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import ReqRunPipeline
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.responses.errors import (
    ServerError as ServerErrorResp,
    MethodNotAllowed,
    Forbidden,
    NotFound,
    BadRequest
)
from backend.errors.api import ServerError
from backend.helpers.PipelineDispatchRequestBuilder import PipelineDispatchRequestBuilder
from backend.services.PipelineDispatcher import service as pipeline_dispatcher
from backend.services.GroupService import service as group_service
from backend.services.SecretService import service as secret_service
from backend.models import  Pipeline


request_builder = PipelineDispatchRequestBuilder(secret_service)

class RunPipeline(RestrictedAPIView):
    def post(self, request, group_id, pipeline_id, *_, **__):
        prepared_request = self.prepare(ReqRunPipeline)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

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


        try:
            # Build the pipeline dispatch request
            pipeline_dispatch_request = request_builder.build(
                request.base_url,
                group,
                pipeline,
                directives=body.directives,
                params=body.params
            )
            
            # Dispatch the request
            pipeline_run = pipeline_dispatcher.dispatch(pipeline_dispatch_request, pipeline)
        except ServerError as e:
            return ServerErrorResp(message=str(e))
        except Exception as e:
            return ServerErrorResp(message=str(e))

        # Respond with the pipeline run
        return ModelResponse(pipeline_run)