from django.db import DatabaseError, IntegrityError, OperationalError

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses import BaseResponse
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

        try:
            PipelineRun.objects.filter(
                uuid=pipeline_run_uuid).update(status=status)
        except (DatabaseError, IntegrityError, OperationalError) as e:
            return ServerError(f"Server Error: {e.__cause__}")
        except Exception as e:
            return ServerError(f"Server Error: {e}")
        
        return BaseResponse(result="TaskExecution status updated")