from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.errors import NotFound, Forbidden
from backend.models import Pipeline
from backend.views.http.responses.BaseResponse import BaseResponse


class ChangePipelineOwner(RestrictedAPIView):
    def patch(self, request, pipeline_id, username):

        # Get the pipeline by the id provided in the path params
        pipeline = Pipeline.objects.filter(id=pipeline_id).first()

        if pipeline is None:
            return NotFound(f"Pipeline not found with id '{pipeline_id}'")

        # Changing ownership is only allowed by the owner
        if request.username != pipeline.owner:
            return Forbidden(message="Change of ownership can only be requested by the current pipeline owner")

        Pipeline.objects.filter(
            id=pipeline_id
        ).update(owner=username)

        return BaseResponse(message=f"Owner for pipeline '{pipeline_id}' updated to {username}")
