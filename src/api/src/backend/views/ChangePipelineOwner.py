from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.errors import NotFound, Forbidden
from backend.models import Pipeline
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.services.GroupService import service as group_service


class ChangePipelineOwner(RestrictedAPIView):
    def patch(self, request, group_id, pipeline_id, username):
        # Get the group
        group = group_service.get(group_id, request.tenant_id)
        if group == None:
            return NotFound(f"No group found with id '{group_id}'")

        # Check that the user belongs to the group
        if not group_service.user_in_group(request.username, group_id, request.tenant_id):
            return Forbidden(message="You do not have access to this group")

        # Get the pipeline by the id provided in the path params
        pipeline = Pipeline.objects.filter(
            group=group,
            id=pipeline_id
        ).first()

        if pipeline is None:
            return NotFound(f"Pipeline not found with id '{pipeline_id}'")

        # Changing ownership is only allowed by the owner
        if request.username != pipeline.owner:
            return Forbidden(message="Change of ownership can only be requested by the current pipeline owner")

        Pipeline.objects.filter(
            id=pipeline_id,
            group=group
        ).update(owner=username)

        return BaseResponse(message=f"Owner for pipeline '{pipeline_id}' updated to {username}")
