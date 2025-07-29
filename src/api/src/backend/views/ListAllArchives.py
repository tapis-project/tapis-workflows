from backend.utils import logger
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.errors import (
    ServerError as ServerErrorResp,
)
from backend.models import GroupUser, Archive
from backend.views.http.responses.models import ModelListResponse

class ListAllArchives(RestrictedAPIView):
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

            archives = []
            for group in groups:
                archives.extend(list(Archive.objects.filter(group=group)))
            
            return ModelListResponse(archives)
        except Exception as e:
            logger.exception(e.__cause__)
            return ServerErrorResp(str(e))