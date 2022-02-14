from django.forms import model_to_dict

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import GroupCreateRequest, GroupPutPatchRequest
from backend.views.http.responses.models import ModelResponse, ModelListResponse
from backend.views.http.responses.errors import ServerError, Conflict, BadRequest, NotFound, Forbidden
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.models import Group, GroupUser


class Groups(RestrictedAPIView):
    def get(self, request, id=None):
        # Get a list of all groups if id is not set
        if id is None:
            return ModelListResponse(Group.objects.all())

        # Return the group by the id provided in the path params
        group = Group.objects.filter(id=id).first()
        if group is None:
            return NotFound(f"Group not found with id '{id}'")

        # Get the group users. Return a 403 if user neither owns the group or
        # belongs to it.
        group_users = group.users.all()
        if (
            request.username != group.owner
            and request.username not in list(filter(lambda u: u.username == request.username, group_users))
        ):
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

        # Create group users for each username passed in the request
        for username in body.users:
            try:
                GroupUser.objects.create(
                    group_id=group.id,
                    username=username
                )
            except Exception as e:
                return BadRequest(message=str(e))
        
        return ModelResponse(group)

    def patch(self, request, id):
        # TODO Handle group.owner changes
        # Validation the request body
        prepared_request = self.prepare(GroupPutPatchRequest)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the json encoded body from the validation result
        body = prepared_request.body

        # Return the group by the id provided in the path params
        group = Group.objects.filter(id=id).first()
        if group is None:
            return NotFound(f"Group not found with id '{id}'")

        # Get the group users. Return a 403 if user neither owns the group or
        # belongs to it.
        group_users = group.users.all()
        if (
            request.username != group.owner
            and request.username not in list(filter(lambda u: u.username == request.username, group_users))
        ):
            return Forbidden("You do not have access to this group")

        # Add all the users from the request that were not previously in it
        modified_group_users = []
        for username in body.users:
            try:
                if username not in [ group_user.username for group_user in group_users ]:
                    group_user = GroupUser.objects.create(
                        group_id=group.id,
                        username=username
                    )
                    modified_group_users.append(group_user)
            except Exception as e:
                return ServerError(message=str(e))

        # Remove all group users that are not in the new users list
        for group_user in group_users:
            try:
                if group_user.username not in body.users:
                    group_user.delete()
                    continue


                modified_group_users.append(group_user)
            except Exception as e:
                return ServerError(message=str(e))
                

        # Convert model into a dict an
        result = model_to_dict(group)
        result["users"] = [ model_to_dict(user) for user in modified_group_users ]
        
        return BaseResponse(result=result)

    def put(self, request, id):
        self.patch(request, id)
        

