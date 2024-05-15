from django.db import DatabaseError, IntegrityError, OperationalError
from django.http import HttpResponse
from django.utils import timezone

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
    PipelineLockAcquisitionResponseSerializer
)
from backend.services.GroupService import service as group_service
from backend.models import Pipeline, PipelineLock, PipelineRun


class PipelineLocksPostDelete(RestrictedAPIView):
    def post(self, request, group_id, pipeline_id, pipeline_run_uuid):
        """Create a lock if not created and attempt to acquire it"""
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
            ).first()

            # Return BadRequest if no pipeline found
            if pipeline == None:
                return BadRequest(f"Pipeline '{pipeline_id}' does not exist")
            
            # Validate the request body based on the type of pipeline specified
            prepared_request = self.prepare(PipelineLockRequest)

            # Return the failure view instance if validation failed
            if not prepared_request.is_valid:
                return prepared_request.failure_view

            # Get the JSON encoded body from the validation result
            body = prepared_request.body

            # Get the pipeline run
            pipeline_run = PipelineRun.objects.filter(
                uuid=pipeline_run_uuid
            ).first()

            # Return BadRequest if no pipeline found
            if pipeline_run == None:
                return BadRequest(f"PipelineRun '{pipeline_run_uuid}' does not exist")

            pipeline_lock = PipelineLock.objects.filter(
                pipeline=pipeline,
                pipeline_run=pipeline_run
            ).first()

            # Create the lock if one does not exist for this pipeline and
            # pipeline run
            if pipeline_lock == None:
                pipeline_lock = PipelineLock.objects.create(
                    pipeline=pipeline,
                    pipeline_run=pipeline_run,
                    expires_in=body.expires_in
                )

            pipeline_lock.pipeline = pipeline
            pipeline_lock.pipeline_run = pipeline_run

            # Start the pipeline locking logic. Refetch the pipeline and its
            # locks and create a list of all competing pipeline runs
            pipeline = Pipeline.objects.filter(
                group=group,
                id=pipeline_id
            ).prefetch_related(
                "pipelinelocks"
            ).first()

            pipeline_locks = pipeline.pipelinelocks.all()
            # Check for the exceptional condition where we successfully fetched
            # or created a pipeline lock in the previous steps above, but for
            # some reason (pipeline, pipeline_run, or pipeline_lock were deleted
            # with exceptional timing) the pipeline lock doesn't exist anymore
            if str(pipeline_lock.uuid) not in [str(lock.uuid) for lock in pipeline_locks]:
                raise Exception(f"PipelineLock with UUID {str(pipeline_lock.uuid)} not found.")

            # This list of pipeline runs competing for a lock on the pipeline
            competing_runs = [lock.pipeline_run for lock in pipeline_locks]

            # Check to see if the pipeline run associated with the current 
            # pipeline lock attempt is the next in the queue. If so, update the
            # pipeline lock's 'acquired_at' property
            if str(pipeline_lock.pipeline_run.uuid) == str(competing_runs[0].uuid):
                pipeline_lock.acquired_at = timezone.now()
                pipeline_lock.save()

            # Set the message for the pipeline lock acquisition attempt
            message = f"Lock not acquired. Locks ahead of '{str(pipeline_lock.uuid)}'"
            if pipeline_lock.acquired_at != None:
                message = f"Pipeline Lock acquired by '{str(pipeline_lock.uuid)}'"

            return BaseResponse(
                status=200,
                success=True,
                message="success",
                result=PipelineLockAcquisitionResponseSerializer.serialize(
                    pipeline_lock,
                    message
                )
            )
            
        except (DatabaseError, IntegrityError, OperationalError) as e:
            logger.exception(e.__cause__)
            return ServerError(message=e.__cause__)
        except Exception as e:
            logger.exception(str(e))
            return ServerError(message=e)

    def delete(self, request, group_id, pipeline_id, pipeline_run_uuid):
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
            ).first()

            # Return BadRequest if no pipeline found
            if pipeline == None:
                return BadRequest(f"Pipeline '{pipeline_id}' does not exist")
            
            # Get the pipeline run
            pipeline_run = PipelineRun.objects.filter(
                uuid=pipeline_run_uuid
            ).first()

            # Return BadRequest if no pipeline found
            if pipeline_run == None:
                return BadRequest(f"PipelineRun '{pipeline_run_uuid}' does not exist")
            
            lock = PipelineLock.objects.filter(
                pipeline=pipeline,
                pipeline_run=pipeline_run
            ).first()

            if lock == None:
                return NotFound(f"PipelineLock not found for pipeline run '{pipeline_run_uuid}' of pipeline '{pipeline_id}'")

            lock.delete()

            return HttpResponse(status=204)
        
        except (DatabaseError, IntegrityError, OperationalError) as e:
            logger.exception(e.__cause__)
            return ServerError(message=e.__cause__)
        except Exception as e:
            logger.exception(str(e))
            return ServerError(message=e)

        