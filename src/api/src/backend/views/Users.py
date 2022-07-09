from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import GroupUserCreateRequest, GroupUserPutPatchRequest
from backend.views.http.responses.models import ModelResponse, ModelListResponse
from backend.views.http.responses.errors import ServerError, NotFound, Forbidden
from backend.views.http.responses import BaseResponse, ResourceURLResponse
from backend.models import Group, GroupUser
from backend.services.GroupService import service as group_service
from backend.helpers import resource_url_builder


class Users(RestrictedAPIView):
    def get(self, request, group_id, username=None):
        "List all users for a group | Get a specified user for a group"
        # Return the group by the id provided in the path params
        group = Group.objects.filter(id=group_id).first()
        if group is None:
            return NotFound(f"Group not found with id '{group_id}'")

        # Get list of all the users in a group
        group_users = GroupUser.objects.filter(group_id=group.id)

        # Get all the group users. Forbid access of requesting user
        # does not belong to the group 
        if request.username not in [ user.username for user in group_users ]:
            return Forbidden("You do not have access to this group")

        # Return the list of group users
        if username is None:
            return ModelListResponse(group_users)

        # Get the specific group user specified in the path params
        group_user = next(filter(lambda user: user.username == username, group_users))
        
        return ModelResponse(group_user)

    def post(self, request, group_id, username=None):
        """Add a user to the group"""
        prepared_request = self.prepare(GroupUserCreateRequest)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

        # Return forbidden if user not admin of group
        if not group_service.user_in_group(request.username, group_id, is_admin=True):
            return Forbidden("You cannot create users for this group")

        # If the user already exists. Do nothing. Return the user.
        group_user = GroupUser.object.filter(username=body.username, group_id=group_id)
        if group_user is not None:
            return ModelResponse(group_user)

        # Create the user
        try:
            group_user = GroupUser.objects.create(
                username=body.username, is_admin=body.is_admin)
        except Exception as e:
            return ServerError(message=str(e))
        
        return ModelResponse(group_user)

    def patch(self, request, group_id, username):
        # TODO Handle group.owner changes
        # Validation the request body
        prepared_request = self.prepare(GroupUserPutPatchRequest)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the json encoded body from the validation result
        body = prepared_request.body

        if not group_service.user_in_group(request.username, group_id, is_admin=True):
            return Forbidden("You cannot update users for this group")

        group_user = GroupUser.objects.filter(
            group_id=group_id,
            username=username
        ).update(
            username=username,
            group_id=group_id,
            is_admin=body.is_admin
        )
        
        return ResourceURLResponse(
            url=resource_url_builder(request.url, group_user.username))

    def put(self, request, group_id, username):
        self.patch(request, group_id, username)

    def delete(self, request, group_id, username):
        # Ensure the requesting user is an admin
        if not group_service.user_in_group(username, group_id, is_admin=True):
            return Forbidden("You cannot delete a user for this group")

        # Owners cannot be deleted
        if group_service.user_owns_group(username, group_id):
            return Forbidden("Users that own groups cannot be removed. Group owner must first be changed")

        group_user = GroupUser.objects.filter(
            group_id=group_id, username=username)

        if group_user == None:
            return NotFound(f"User not found with username '{username}' in group '{group_id}'")

        # Only group owners can delete group admins
        if (
            group_user.is_admin 
            and not group_service.user_owns_group(request.username, group_id)
        ):
            return Forbidden("Only group owners can delete admin users")

        # Delete the user
        group_user.delete()

        return BaseResponse(message="Success")

        


        

