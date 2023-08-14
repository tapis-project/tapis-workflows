from django.db import DatabaseError, IntegrityError, OperationalError
from django.utils import timezone

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import PipelineRun
from backend.views.http.responses import BaseResponse, BadRequest
from backend.views.http.responses.errors import (
    ServerError,
    BadRequest
)
from backend.models import PipelineRun
from backend.utils import executor_request_is_valid


class UpdatePipelineRunStatus(RestrictedAPIView):
    def patch(self, request, pipeline_run_uuid, status, *_,  **__):
        if not executor_request_is_valid(request):
            return BadRequest(message=f"X-WORKFLOW-EXECUTOR-TOKEN header is invalid")
        
        prepared_request = self.prepare(PipelineRun, uuid=pipeline_run_uuid)
        
        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view
        
        # Get the JSON encoded body from the validation result
        body = prepared_request.body

        try:
            PipelineRun.objects.filter(
                uuid=pipeline_run_uuid).update(
                    status=status,
                    last_modified=timezone.now(),
                    logs=body.logs
                )
        except (DatabaseError, IntegrityError, OperationalError) as e:
            return ServerError(f"Server Error: {e.__cause__}")
        except Exception as e:
            return ServerError(f"Server Error: {e}")
        
        return BaseResponse(result="Pipeline Run updated")