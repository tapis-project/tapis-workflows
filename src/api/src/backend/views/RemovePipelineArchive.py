from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses import BaseResponse
from backend.views.http.responses.errors import Forbidden, NotFound
from backend.views.http.requests import AddRemoveArchive
from backend.models import PipelineArchive, Pipeline, Archive
from backend.services.GroupService import service as group_service


class RemovePipelineArchive(RestrictedAPIView):
    def delete(self, request, group_id, pipeline_id):
        # Get the group
        group = group_service.get(group_id, request.tenant_id)
        if group == None:
            return NotFound(f"No group found with id '{group_id}'")

        # Check that the user belongs to the group
        if not group_service.user_in_group(request.username, group_id, request.tenant_id):
            return Forbidden(message="You do not have access to this group")

        # Get the pipeline by the id provided in the path params
        pipeline = Pipeline.objects.filter(
            id=pipeline_id,
            group=group
        ).first()

        if pipeline == None:
            return NotFound(f"Pipeline not found with id '{pipeline_id}'")

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

        # Check that id of the pipeline is unique
        pipeline_archive = PipelineArchive.objects.filter(
            pipeline=pipeline,
            archive=archive
        )

        if pipeline_archive != None:
            pipeline_archive.delete()

        return BaseResponse(message=f"Archive '{body.archive_id}' removed from pipeline '{pipeline_id}'")

