import json, pprint

from django.db import IntegrityError, OperationalError, DatabaseError

from backend.models import Secret
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.secrets import ReqCreateSecret
from backend.views.http.responses import BaseResponse, NoContentResponse
from backend.views.http.responses.errors import BadRequest, Forbidden, NotFound, MethodNotAllowed, ServerError, Conflict
from backend.views.http.responses import BaseResponse
from backend.services.SecretService import service as secret_service
from backend.serializers import SecretSerializer
from backend.helpers import resource_url_builder
from backend.utils import logger


class Secrets(RestrictedAPIView):
    def get(self, request, secret_id=None):
        try:
            if secret_id == None:
                return self.list(request.username, request.tenant_id)

            # Get the secret
            secret = Secret.objects.filter(
                id=secret_id,
                tenant_id=request.tenant_id,
                owner=request.username,
            ).first()

            # Return if BadRequest if no secret found
            if secret == None:
                return BadRequest(f"Secret with id '{secret_id}' does not exist for user '{request.username}'")
            
            return BaseResponse(result=SecretSerializer.serialize(secret))
        except Exception as e:
            logger.exception(e.__cuase__)
            return ServerError(str(e))

    def list(self, username, tenant_id, *_, **__):
        secrets = []
        try:
            secret_models = Secret.objects.filter(owner=username, tenant_id=tenant_id)
            for secret_model in secret_models:
                secrets.append(SecretSerializer.serialize(secret_model))
            
            return BaseResponse(result=secrets)
        except Exception as e:
            logger.exception(e.__cause__)
            return ServerError(f"{e}")

    def post(self, request, *_, **__):
        # Validate and prepare the create reqeust
        prepared_request = self.prepare(ReqCreateSecret)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        req_secret = prepared_request.body

        # Check if secret exists
        if Secret.objects.filter(id=req_secret.id, owner=request.username, tenant_id=request.tenant_id).exists():
            return Conflict(f"A secret already exists for owner '{request.username}' with the id '{req_secret.id}'")

        # Create secret
        try:
            secret = secret_service.create(request.tenant_id, request.username, req_secret)
        except (IntegrityError, OperationalError, DatabaseError) as e:
            logger.exception(e.__cause__)
            return ServerError(message=e.__cause__)
        except Exception as e:
            logger.exception(e.__cause__)
            return ServerError(f"{e}")

        return BaseResponse(result=SecretSerializer.serialize(secret))

    def put(self, *_, **__):
        return MethodNotAllowed("Method 'PUT' not allowed for 'Secret' objects")
    
    def patch(self, *_, **__):
        return MethodNotAllowed("Method 'PATCH' not allowed for 'Secret' objects")

    def delete(self, request, secret_id):
        # Get the secret
        secret = Secret.objects.filter(
            owner=request.username,
            tenant_id=request.tenant_id,
            id=secret_id
        ).first()

        if secret == None:
            return NotFound(f"Secret with id '{secret_id}' not found for user {request.username}'")
        
        # Only secret owners can delete the secret
        if request.username != secret.owner:
            return Forbidden(message="Only secret owners can delete a secret")

        try:
            secret_service.delete(secret_id=secret.id, tenant_id=request.tenant_id, owner=secret.owner)
        except Exception as e:
            logger.exception(e.__cause__)
            return ServerError(str(e))

        return NoContentResponse(message=f"Deleted secret '{secret_id}'")

        