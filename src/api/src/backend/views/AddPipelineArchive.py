from django.db import DatabaseError, IntegrityError, OperationalError

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses import BaseResponse
from backend.views.http.responses.errors import Forbidden, NotFound, BadRequest
from backend.views.http.requests import AddRemoveArchive
from backend.models import Archive, PipelineArchive, Pipeline
from backend.services.GroupService import service as group_service


class AddPipelineArchive(RestrictedAPIView):
    def post(self, request, group_id, pipeline_id):
        # Check that the user belongs to the group that owns this archive
        if not group_service.user_in_group(request.username, group_id):
            return Forbidden(message="You do not have access to this pipeline")

        # Validate the request body based on the type of pipeline specified
        prepared_request = self.prepare(AddRemoveArchive)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = prepared_request.body

        # Get the pipeline
        pipeline = Pipeline.objects.filter(
            group_id=group_id, id=pipeline_id).first()

        if pipeline == None:
            return NotFound(message=f"Pipeline '{pipeline_id}' does not exist for group '{group_id}'")

        # Get the archive
        archive = Archive.objects.filter(
            group_id=group_id, id=body.archive_id).first()

        if archive == None:
            return NotFound(message=f"Archive '{body.archive_id}' does not exist for group '{group_id}'")

        # Repsond with archive not found
        if archive == None:
            return NotFound(message=f"Archive '{body.archive_id}' not found in group '{group_id}'")

        try:
            # Create the pipeline_archive
            PipelineArchive.objects.create(
                archive=archive,
                pipeline=pipeline
            )
        except (DatabaseError, IntegrityError, OperationalError) as e:
            return BadRequest(message=e)

        return BaseResponse(message=f"Archive '{body.archive_id}' added to pipeline '{pipeline_id}'")

