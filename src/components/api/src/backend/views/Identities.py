from django.db import IntegrityError

from backend.models import Identity, CONTEXT_TYPES
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.responses.errors import BadRequest
from backend.views.http.requests import IdentityCreateRequest
from backend.services.CredentialService import CredentialService


IDENTITY_TYPES = [ identity_type[0] for identity_type in CONTEXT_TYPES ]

class Identities(RestrictedAPIView):
    def get(self, request):

        identities = Identity.objects.filter(owner=request.username)

        return ModelListResponse(identities)

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
            cred_service = CredentialService()
            credentials = cred_service.save(request.username, body.credentials)
        except Exception as e:
            return BadRequest(message=e)

        try:
            identity = Identity.objects.create(
                type=body.type,
                owner=request.username,
                credentials=credentials
            )
        except IntegrityError as e:
            cred_service.delete(credentials.sk_id)
            return BadRequest(message=e.__cause__)

        return ModelResponse(identity)