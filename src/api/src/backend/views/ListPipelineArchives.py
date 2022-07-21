from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.models import ModelListResponse
from backend.views.http.responses.errors import Forbidden, NotFound, BadRequest
from backend.models import PipelineArchive, Pipeline
from backend.services.GroupService import service as group_service


class ListPipelineArchives(RestrictedAPIView):
    def get(self, request, group_id, pipeline_id):
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
        
        # Get the archive
        pipeline_archives = PipelineArchive.objects.filter(
            pipeline=pipeline
        ).prefetch_related("archive")

        archives = []
        for pipeline_archive in pipeline_archives:
            archives.append(pipeline_archive.archive)

        return ModelListResponse(archives)