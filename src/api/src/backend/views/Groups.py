from django.forms import model_to_dict
from django.db import DatabaseError, IntegrityError, OperationalError

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import GroupCreateRequest
from backend.views.http.responses.models import ModelListResponse
from backend.views.http.responses.errors import ServerError, Conflict, BadRequest, NotFound, Forbidden
from backend.views.http.responses import BaseResponse, ResourceURLResponse
from backend.models import Group, GroupUser
from backend.helpers import resource_url_builder
from backend.services.GroupService import service as group_service
from backend.utils import logger

# TODO Rollbacks on failture
class Groups(RestrictedAPIView):
    def get(self, request, group_id=None):
        # Get a list of all groups the user belongs to
        if group_id == None:
            return self.list(request)

        # Return the group by the id provided in the path params
        group = Group.objects.filter(
            id=group_id,
            tenant_id=request.tenant_id
        ).first()

        if group == None:
            return NotFound(f"Group not found with id '{group_id}'")

        # Get the group users. Return a 403 if user doesn't belong to the group
        group_users = group.users.all()
        if request.username not in [user.username for user in group_users]:
            return Forbidden("You do not have access to this group")

        # Convert model into a dict an
        result = model_to_dict(group)
        result["users"] = [model_to_dict(user) for user in group_users]
        
        return BaseResponse(result=result)

    def list(self, request):
        # Get all of the GroupUser objects with the requesting user's username
        group_users = GroupUser.objects.filter(
            username=request.username).prefetch_related("group")

        # Get all the groups to which the request user belongs
        groups = []
        for user in group_users:
            if user.group.tenant_id == request.tenant_id:
                groups.append(user.group)
        
        return ModelListResponse(groups)
    
    def delete(self, request, group_id):
        try:
            # Get the group
            group = group_service.get(group_id, request.tenant_id)
            if group == None:
                return NotFound(f"No group found with id '{group_id}'")
            
            if request.username != group.owner:
                return Forbidden(message="Groups can only be delete by the group owner")
            
            group.delete()
        
            return BaseResponse(result=f"Group {group_id} successfully delete")
        
        except (DatabaseError, IntegrityError, OperationalError) as e:
            logger.exception(e.__cause__)
            return ServerError(message=e.__cause__)
        except Exception as e:
            logger.exception(str(e))
            return ServerError(str(e))
        

    def post(self, request, **_):
        try:
            prepared_request = self.prepare(GroupCreateRequest)

            if not prepared_request.is_valid:
                return prepared_request.failure_view

            body = prepared_request.body

            # Check that id of the group is unique
            existing_group = Group.objects.filter(id=body.id, tenant_id=request.tenant_id).first()
            print(model_to_dict(existing_group))
            if existing_group != None:
                return Conflict(f"A Group already exists with the id '{body.id}'")

            # Save the Group object to the database
            group = Group.objects.create(
                id=body.id, owner=request.username, tenant_id=request.tenant_id)
        
            # Create an admin group user for the requesting user
            GroupUser.objects.create(
                group=group,
                username=request.username,
                is_admin=True
            )


            # Create group users for each username passed in the request
            for user in body.users:
                # Do not create a group user for the requesting user
                if user.username != request.username:
                    GroupUser.objects.create(
                        group=group,
                        username=user.username,
                        is_admin=user.is_admin
                    )

            return ResourceURLResponse(
                url=resource_url_builder(request.url, group.id))
        
        except (DatabaseError, IntegrityError, OperationalError) as e:
            logger.exception(e.__cause__)
            return ServerError(message=e.__cause__)
        except Exception as e:
            logger.exception(str(e))
            return ServerError(str(e))
        