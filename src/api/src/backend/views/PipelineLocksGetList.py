from django.db import DatabaseError, IntegrityError, OperationalError

from backend.utils import logger
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.errors import (
    ServerError,
    Forbidden,
    NotFound,
    BadRequest
)
from backend.views.http.requests import PipelineLockRequest
from backend.serializers import (
    PipelineLockModelSerializer
)
from backend.services.GroupService import service as group_service
from backend.models import Pipeline

class PipelineLocksGetList(RestrictedAPIView):
    def get(self, request, group_id, pipeline_id, pipeline_lock_uuid=None, *_,  **__):
        try:
            # Get the group
            group = group_service.get(group_id, request.tenant_id)
            if group == None:
                return NotFound(f"No group found with id '{group_id}'")

            # Check that the user belongs to the group
            if not group_service.user_in_group(request.username, group_id, request.tenant_id):
                return Forbidden(message="You do not have access to this group")

            # Get the pipeline
            pipeline = Pipeline.objects.filter(
                group=group,
                id=pipeline_id
            ).prefetch_related(
                "pipelinelocks"
            ).first()

            # Return if BadRequest if no pipeline found
            if pipeline == None:
                return BadRequest(f"Pipeline '{pipeline_id}' does not exist")

            # If no pipeline_lock_uuid is provided, then list all pipeline
            # locks for this pipeline
            if pipeline_lock_uuid == None:
                return self.list(pipeline)

            lock_model = next(
                filter(
                    lambda lock: str(lock.uuid) == pipeline_lock_uuid,
                    pipeline.pipelinelocks.all()
                ),
                None
            )

            if lock_model == None:
                return BadRequest(f"PipelineLock with uuid '{pipeline_lock_uuid}' does not exist")

            # Serialize the PipelineLock model instance
            lock = PipelineLockModelSerializer.serialize(lock_model, pipeline)

            return BaseResponse(
                status=200,
                success=True,
                message="success",
                result=lock
            )
            
        # TODO catch the specific error thrown by the group service
        except (DatabaseError, IntegrityError, OperationalError) as e:
            logger.exception(e.__cause__)
            return ServerError(message=e.__cause__)
        except Exception as e:
            logger.exception(str(e))
            return ServerError(message=e)

    def list(self, pipeline):
        serialized_locks = []
        try:
            locks = pipeline.pipelinelocks.all()

            for lock in locks:
                serialized_lock = PipelineLockModelSerializer.serialize(
                    lock,
                    pipeline
                )
                serialized_locks.append(serialized_lock)

            return BaseResponse(
                status=200,
                success=True,
                message="success",
                result=serialized_locks
            )
        except (DatabaseError, IntegrityError, OperationalError) as e:
            logger.exception(e.__cause__)
            return ServerError(message=e.__cause__)
        except Exception as e:
            logger.exception(str(e))
            return ServerError(message=e)

        