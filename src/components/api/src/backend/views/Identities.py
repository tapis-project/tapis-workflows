from django.db import IntegrityError

from backend.models import Identity, IDENTITY_TYPES
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.models import ModelListResponse, ModelResponse, BaseResponse
from backend.views.http.responses.errors import BadRequest, NotFound, Forbidden
from backend.views.http.requests import IdentityCreateRequest
from backend.services import CredentialsService


IDENTITY_TYPES = [ identity_type[0] for identity_type in IDENTITY_TYPES ]

class Identities(RestrictedAPIView):
    def get(self, request, identity_uuid=None):

        if identity_uuid is None:
            identities = Identity.objects.filter(owner=request.username)
            return ModelListResponse(identities)

        identity = Identity.objects.filter(pk=identity_uuid).first()
        if identity == None:
            return NotFound("Identity not found")

        if identity.owner != request.owner:
            return Forbidden("You do not have access to this identity")

        return ModelResponse(identity)

    def post(self, request, *args, **kwargs):
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

        # Persist the credentials in sk
        try:
            cred_service = CredentialsService()
            credentials = cred_service.save(request.username, body.credentials)
        except Exception as e:
            return BadRequest(message=e)

        try:
            identity = Identity.objects.create(
                name=body.name,
                description=body.description,
                type=body.type,
                owner=request.username,
                credentials=credentials
            )
        except IntegrityError as e:
            cred_service.delete(credentials.sk_id)
            return BadRequest(message=e.__cause__)

        return ModelResponse(identity)

    def delete(self, request, identity_uuid):
        identity = Identity.objects.filter(pk=identity_uuid).first()

        if identity == None:
            return NotFound("Identity does not exist")

        # Requesting user can only delete their own identities
        if identity.owner != request.username:
            return Forbidden("You do not have access to this identity")

        identity.delete()

        return BaseResponse(message="Identity deleted successfully")
