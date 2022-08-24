from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import GroupUserCreateRequest, GroupUserPutPatchRequest
from backend.views.http.responses.models import ModelResponse, ModelListResponse
from backend.views.http.responses.errors import ServerError, NotFound, Forbidden, UnprocessableEntity
from backend.views.http.responses import BaseResponse, ResourceURLResponse
from backend.models import Group, GroupUser
from backend.services.GroupService import service as group_service
from backend.helpers import resource_url_builder


class Users(RestrictedAPIView):
    def get(self, request, group_id, username=None):
        "List all users for a group | Get a specified user for a group"
        # Get the group
        group = group_service.get(group_id, request.tenant_id)
        if group == None:
            return NotFound(f"No group found with id '{group_id}'")

        # Check that the user belongs to the group
        if not group_service.user_in_group(request.username, group_id, request.tenant_id):
            return Forbidden(message="You do not have access to this group")

        # Get list of all the users in a group
        group_users = GroupUser.objects.filter(group=group)

        # Return the list of group users
        if username is None:
            return ModelListResponse(group_users)

        # Get the specific group user specified in the path params
        group_user = next(filter(lambda user: user.username == username, group_users))
        
        return ModelResponse(group_user)

    def post(self, request, group_id, **_):
        """Add a user to the group"""
        # Get the group
        group = group_service.get(group_id, request.tenant_id)
        if group == None:
            return NotFound(f"No group found with id '{group_id}'")

        # Check that the user belongs to the group
        if not group_service.user_in_group(
            request.username, group_id, request.tenant_id, is_admin=True):
            return Forbidden(message="You cannot add users to this group")

        prepared_request = self.prepare(GroupUserCreateRequest)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

        # If the user already exists. Do nothing. Return the user.
        group_user = GroupUser.objects.filter(username=body.username, group=group).first()
        if group_user != None:
            return ResourceURLResponse(
                url=resource_url_builder(request.url, group_user.username))

        # Create the user
        try:
            group_user = GroupUser.objects.create(
                username=body.username,
                group=group,
                is_admin=body.is_admin
            )
        except Exception as e:
            return ServerError(message=str(e))
        
        return ResourceURLResponse(
            url=resource_url_builder(request.url, group_user.username))

    def patch(self, request, group_id, username):
        # Get the group
        group = group_service.get(group_id, request.tenant_id)
        if group == None:
            return NotFound(f"No group found with id '{group_id}'")

        # Check that the user belongs to the group
        if not group_service.user_in_group(
            request.username, group_id, request.tenant_id, is_admin=True):
            return Forbidden(message="You cannot update users in this group")

        # Validation the request body
        prepared_request = self.prepare(GroupUserPutPatchRequest)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the json encoded body from the validation result
        body = prepared_request.body

        group_user = GroupUser.objects.filter(
            group=group,
            username=username
        ).first().update(
            username=username,
            group=group,
            is_admin=body.is_admin
        )
        
        return ResourceURLResponse(
            url=resource_url_builder(request.url, group_user.username))

    def put(self, request, group_id, username):
        self.patch(request, group_id, username)

    def delete(self, request, group_id, username):
        # Get the group
        group = group_service.get(group_id, request.tenant_id)
        if group == None:
            return NotFound(f"No group found with id '{group_id}'")

        # Check that the user belongs to the group
        if not group_service.user_in_group(
            request.username, group_id, request.tenant_id, is_admin=True):
            return Forbidden(message="You cannot delete users from this group")

        # Owners cannot be deleted
        if group_service.user_owns_group(username, group_id):
            return UnprocessableEntity("Users that own groups cannot be removed. Group owner must first be changed")

        group_user = GroupUser.objects.filter(
            group=group, username=username).first()

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

        return BaseResponse(message="User deleted")

        


        

