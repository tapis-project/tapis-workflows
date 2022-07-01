from django.forms import model_to_dict

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import GroupCreateRequest
from backend.views.http.responses.models import ModelResponse, ModelListResponse
from backend.views.http.responses.errors import ServerError, Conflict, BadRequest, NotFound, Forbidden
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.models import Group, GroupUser


class Groups(RestrictedAPIView):
    def get(self, request, group_id=None):
        # Get a list of all groups the user belongs to
        if group_id is None:
            group_users = GroupUser.objects.filter(username=request.username)
            group_ids = [ user.group_id for user in group_users ]
            return ModelListResponse(Group.objects.filter(id__in=group_ids))

        # Return the group by the id provided in the path params
        group = Group.objects.filter(id=group_id).first()
        if group is None:
            return NotFound(f"Group not found with id '{group_id}'")

        # Get the group users. Return a 403 if user doesn't belong to the group
        group_users = group.users.all()
        if request.username != [ user.username for user in group_users ]:
            return Forbidden("You do not have access to this group")

        # Convert model into a dict an
        result = model_to_dict(group)
        result["users"] = [ model_to_dict(user) for user in group_users ]
        
        return BaseResponse(result=result)

    def post(self, request, **_):
        prepared_request = self.prepare(GroupCreateRequest)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

        # Check that id of the group is unique
        if Group.objects.filter(id=body.id).exists():
            return Conflict(f"A Group already exists with the id '{body.id}'")

        try:
            # Save the Group object to the database
            group = Group.objects.create(id=body.id, owner=request.username)
        except Exception as e:
            return ServerError(message=str(e))

        # Create an admin group user for the requesting user
        try:
            GroupUser.objects.create(
                group_id=group.id,
                username=request.username,
                is_admin=True
            )
        except Exception as e:
            return ServerError(message=str(e))

        # Create group users for each username passed in the request
        for user in body.users:
            try:
                # Do not create a group user for the requesting user
                if user.username != request.username:
                    GroupUser.objects.create(
                        group_id=group.id,
                        username=user.username,
                        is_admin=user.is_admin
                    )
            except Exception as e:
                return BadRequest(message=str(e))
        
        return ModelResponse(group)
        