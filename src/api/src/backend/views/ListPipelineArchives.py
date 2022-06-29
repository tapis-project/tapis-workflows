from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.models import ModelListResponse
from backend.views.http.responses.errors import Forbidden, NotFound
from backend.models import PipelineArchive, Pipeline
from backend.services import group_service


class ListPipelineArchives(RestrictedAPIView):
    def get(self, request, group_id, pipeline_id):
        # Check that the user belongs to the group that owns this archive
        if not group_service.user_in_group(request.username, group_id):
            return Forbidden(message="You do not have access to this pipeline")

        # Get the pipeline
        pipeline = Pipeline.objects.filter(
            group_id=group_id, id=pipeline_id).first()

        if pipeline == None:
            return NotFound(message=f"Pipeline '{pipeline_id}' does not exist for group '{group_id}'")
        
        # Get the archive
        pipeline_archives = PipelineArchive.objects.filter(
            pipeline=pipeline
        ).prefetch_related("archive")

        archives = []
        for pipeline_archive in pipeline_archives:
            archives.append(pipeline_archive.archive)

        return ModelListResponse(archives)