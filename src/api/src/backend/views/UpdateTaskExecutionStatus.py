from django.db import DatabaseError, IntegrityError, OperationalError
from django.utils import timezone

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import ReqPatchTaskExecution
from backend.views.http.responses import BaseResponse
from backend.views.http.responses.errors import (
    BadRequest,
    ServerError
)
from backend.models import TaskExecution
from backend.utils import executor_request_is_valid


class UpdateTaskExecutionStatus(RestrictedAPIView):
    def patch(self, request, task_execution_uuid, status, *_,  **__):
        if not executor_request_is_valid(request):
            return BadRequest(message=f"X-WORKFLOW-EXECUTOR-TOKEN header is invalid")
        
        prepared_request = self.prepare(ReqPatchTaskExecution, uuid=task_execution_uuid)
        
        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view
        
        # Get the JSON encoded body from the validation result
        body = prepared_request.body

        try:
            TaskExecution.objects.filter(
                uuid=task_execution_uuid).update(
                    status=status,
                    last_modified=timezone.now(),
                    last_message=body.last_message,
                    stdout=body.stdout,
                    stderr=body.stderr
                )
            
            return BaseResponse(result="TaskExecution status updated")
    
        except (DatabaseError, IntegrityError, OperationalError) as e:
            return ServerError(f"Server Error: {e.__cause__}")
        except Exception as e:
            return ServerError(f"Server Error: {e}")
        