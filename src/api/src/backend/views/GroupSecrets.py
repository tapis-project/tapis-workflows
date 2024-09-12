from django.db import IntegrityError, OperationalError, DatabaseError

from backend.models import GroupSecret, Secret
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses import BaseResponse, NoContentResponse
from backend.views.http.responses.errors import BadRequest, Forbidden, NotFound, MethodNotAllowed, ServerError, Conflict
from backend.views.http.responses import BaseResponse
from backend.services.GroupService import service as group_service
from backend.serializers import GroupSecretSerializer
from backend.utils import logger


class GroupSecrets(RestrictedAPIView):
    def get(self, request, group_id, group_secret_id=None):
        try:
            # Get the group
            group = group_service.get(group_id, request.tenant_id)
            if group == None:
                return NotFound(f"No group found with id '{group_id}'")

            # Check that the user belongs to the group
            if not group_service.user_in_group(request.username, group_id, request.tenant_id):
                return Forbidden(message="You do not have access to this group")

            # Return a GroupSecretList response
            if group_secret_id == None:
                return self.list(group)
            
            # Get the group secret by id
            group_secret = GroupSecret.objects.filter(
                id=group_secret_id,
                group=group
            ).prefetch_related("secret", "group").first()

            # Return if NotFound if no group secret found with the provided id
            if group_secret == None:
                return NotFound(f"GroupSecret with id '{group_secret_id}' does not exist does in group '{group.id}'")
            
            return BaseResponse(result=GroupSecretSerializer.serialize(group_secret))
        except Exception as e:
            logger.exception(e.__cuase__)
            return ServerError(str(e))

    def list(self, group, *_, **__):
        group_secrets = []
        try:
            group_secret_models = GroupSecret.objects.filter(
                group=group
            ).prefetch_related("secret", "group").all()

            for group_secret_model in group_secret_models:
                group_secrets.append(GroupSecretSerializer.serialize(group_secret_model))
            
            return BaseResponse(result=group_secrets)
        except Exception as e:
            logger.exception(e.__cause__)
            return ServerError(f"{e}")

    def post(self, request, group_id, *_, **__):
        try:
            secret_id = self.request_body.get("secret_id")
            if secret_id == None:
                return BadRequest("Property 'secret_id' missing from request")
            
            # Get the group
            group = group_service.get(group_id, request.tenant_id)
            if group == None:
                return NotFound(f"No group found with id '{group_id}'")

            # Check that the user belongs to the group
            if not group_service.user_in_group(request.username, group_id, request.tenant_id):
                return Forbidden(message="You do not have access to this group")
            
            # Fetch the secret
            secret = Secret.objects.filter(
                id=secret_id,
                tenant_id=request.tenant_id,
                owner=request.username
            ).first()

            if secret == None:
                return NotFound(message=f"No secret found with id '{secret_id}'")
            
            group_secret_id = self.request_body.get("id")
            if group_secret_id == None:
                group_secret_id = secret.id

            if GroupSecret.objects.filter(group=group, id=group_secret_id).exists():
                return Conflict(message=f"A GroupSecret already exists with id '{group_secret_id}'")

            # Create group secret
            group_secret = GroupSecret.objects.create(
                id=group_secret_id,
                group=group,
                secret=secret
            )

            return BaseResponse(result=GroupSecretSerializer.serialize(group_secret))
        
        except (IntegrityError, OperationalError, DatabaseError) as e:
            return BadRequest(message=e.__cause__)
        except Exception as e:
            logger.exception(e.__cause__)
            return ServerError(f"{e}")

    def put(self, *_, **__):
        return MethodNotAllowed("Method 'PUT' not allowed for 'GroupSecret' objects")
    
    def patch(self, *_, **__):
        return MethodNotAllowed("Method 'PATCH' not allowed for 'GroupSecret' objects")

    def delete(self, request, group_id, group_secret_id):
        try:
            # Get the group
            group = group_service.get(group_id, request.tenant_id)
            if group == None:
                return NotFound(f"No group found with id '{group_id}'")

            # Check that the user belongs to the group
            if not group_service.user_in_group(request.username, group_id, request.tenant_id):
                return Forbidden(message="You do not have access to this group")

            # Get the group secret
            group_secret = GroupSecret.objects.filter(
                group=group,
                id=group_secret_id
            ).prefetch_related("secret").first()

            if group_secret == None:
                return NotFound(f"Secret with id '{group_secret_id}' not found in group '{group.id}'")
            
            # Only group_secret owners can delete the group_secret
            if (
                request.username != group_secret.secret.owner
                and not group_service.user_in_group(request.username, group_id, request.tenant_id, is_admin=True)
            ):
                return Forbidden(message="Only GroupSecret owners and group admins can delete a GroupSecret")

            group_secret.delete()
        except Exception as e:
            logger.exception(e.__cause__)
            return ServerError(str(e))

        return NoContentResponse(message=f"Deleted GroupSecret '{group_secret_id}' from group '{group.id}")

        