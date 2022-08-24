from django.db import IntegrityError

from backend.models import Identity, IDENTITY_TYPES
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.models import ModelListResponse, ModelResponse, BaseResponse
from backend.views.http.responses.errors import BadRequest, NotFound, Forbidden, ServerError
from backend.views.http.responses import ResourceURLResponse
from backend.views.http.requests import IdentityCreateRequest
from backend.services.SecretService import service as secret_service
from utils.cred_validators import validate_by_type
from backend.helpers import resource_url_builder


IDENTITY_TYPES = [ identity_type[0] for identity_type in IDENTITY_TYPES ]

class Identities(RestrictedAPIView):
    def get(self, request, identity_uuid=None):

        if identity_uuid is None:
            identities = Identity.objects.filter(owner=request.username)
            return ModelListResponse(identities)

        identity = Identity.objects.filter(pk=identity_uuid).first()
        if identity == None:
            return NotFound("Identity not found")

        if request.username != identity.owner:
            return Forbidden("You do not have access to this identity")

        return ModelResponse(identity)

    def post(self, request, *_, **__):
        # Validate the request body
        self.prepare(IdentityCreateRequest)

        # Return the failure view instance if validation failed
        if not self.prepared_request.is_valid:
            return self.prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = self.prepared_request.body

        # Return bad request if invalid identity type
        if body.type not in IDENTITY_TYPES:
            return BadRequest(f"Invalid type for identity. Recieved: {body.type} - Expected one of the following: {IDENTITY_TYPES}")

        # Validate the credentials
        try:
            is_valid = validate_by_type(body.type, body.credentials)
        except Exception as e:
            return ServerError("An error has occured when validating the identity credentials")

        if not is_valid:
            return BadRequest(f"Bad Credentials: The '{body.type}' credentials provided are invalid")

        # Persist the credentials in sk
        try:
            credentials = secret_service.save(request.username, body.credentials)
        except Exception as e:
            return BadRequest(message=e)

        try:
            identity = Identity.objects.create(
                name=body.name,
                description=body.description,
                type=body.type,
                owner=request.username,
                credentials=credentials,
                tenant_id=request.tenant_id
            )
        except IntegrityError as e:
            secret_service.delete(credentials.sk_id)
            return BadRequest(message=e.__cause__)

        return ResourceURLResponse(
            url=resource_url_builder(request.url, str(identity.uuid)))

    def delete(self, request, identity_uuid):
        identity = Identity.objects.filter(
            pk=identity_uuid
        ).prefetch_related(
            "credentials"
        ).first()

        if identity == None:
            return NotFound("Identity does not exist")

        # Requesting user can only delete their own identities
        if identity.owner != request.username:
            return Forbidden("You do not have access to this identity")

        secret_service.delete(identity.credentials.sk_id)

        identity.delete()

        # TODO Delete the credentials for the identity in SK
        msg = "Identity deleted successfully"
        return BaseResponse(result=msg, message=msg)
