from backend.utils import logger
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.errors import (
    ServerError as ServerErrorResp,
)
from backend.serializers import PipelineSerializer
from backend.models import GroupUser, Pipeline
from backend.views.http.responses import BaseResponse

class ListAllPipelines(RestrictedAPIView):
    def get(self, request):
        try:
            # Get all of the GroupUser objects with the requesting user's username
            group_users = GroupUser.objects.filter(
                username=request.username).prefetch_related("group")

            # Get all the groups to which the request user belongs
            groups = []
            for user in group_users:
                if user.group.tenant_id == request.tenant_id:
                    groups.append(user.group)

            pipelines = []
            for group in groups:
                pipelines.extend(list(Pipeline.objects.filter(group=group)))

            # Convert all of the pipeline pipelines and task models into a dict
            result = []
            for pipeline in pipelines:
                tasks = pipeline.tasks.all()
                result.append(PipelineSerializer.serialize(pipeline, tasks)) 
            
            return BaseResponse(result=result)
        except Exception as e:
            logger.exception(e.__cause__)
            return ServerErrorResp(str(e))