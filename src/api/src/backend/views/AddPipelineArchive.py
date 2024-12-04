from django.db import DatabaseError, IntegrityError, OperationalError

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses import BaseResponse
from backend.views.http.responses.errors import Forbidden, NotFound, BadRequest
from backend.views.http.requests import AddRemoveArchive
from backend.models import Archive, PipelineArchive, Pipeline
from backend.services.GroupService import service as group_service


class AddPipelineArchive(RestrictedAPIView):
    def post(self, request, group_id, pipeline_id):
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
            return BadRequest(f"Pipline with id '{pipeline_id}' does not exist")

        # Validate the request body based on the type of pipeline specified
        prepared_request = self.prepare(AddRemoveArchive)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = prepared_request.body

        # Get the archive
        archive = Archive.objects.filter(
            group=group, id=body.archive_id).first()

        if archive == None:
            return NotFound(message=f"Archive '{body.archive_id}' does not exist for group '{group_id}'")

        try:
            # Create the pipeline_archive
            PipelineArchive.objects.create(
                archive=archive,
                pipeline=pipeline
            )
        except (DatabaseError, IntegrityError, OperationalError) as e:
            return BadRequest(message=e)

        return BaseResponse(message=f"Archive '{body.archive_id}' added to pipeline '{pipeline_id}'")

