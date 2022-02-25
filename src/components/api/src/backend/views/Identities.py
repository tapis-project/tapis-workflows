from django.db import IntegrityError

from backend.models import Identity, CONTEXT_TYPES
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.responses.errors import BadRequest
from backend.views.http.requests import IdentityCreateRequest
from backend.services.GroupService import service


IDENTITY_TYPES = [ identity_type[0] for identity_type in CONTEXT_TYPES ]

class Identities(RestrictedAPIView):
    def get(self, request):
        identities = Identity.objects.all()

        return ModelListResponse(identities)

    def post(self, request):
        # Validate the request body
        self.prepare(IdentityCreateRequest)

        # Return the failure view instance if validation failed
        if not self.prepared_request.is_valid:
            return self.prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = self.prepared_request.body

        # Determine if a user is creating an identity for themselves, or
        # on behalf of another user as a group owner
        on_behalf_of = body.username == request.username

        # Fetch the group
        group = service.get(body.group_id)

        # Return bad request if group does not exist
        if group is None:
            return BadRequest(f"Group with id '{body.group_id}' does not exist")

        # Return bad request if invalid identity type
        if body.type not in IDENTITY_TYPES:
            return BadRequest(f"Invalid type for identity. Recieved: {body.type} - Expected one of the following: {IDENTITY_TYPES}")

        # Return bad request is user is unable to create an identity themselves in this group
        # or for another user if they are not the group owner
        if (
            not service.user_in_group(body.username, group.id)
            or (on_behalf_of and not service.user_owns_group(request.username, body.group_id))
        ):
            return BadRequest(message=f"You cannot create an identity for user '{body.username}' for group '{body.group_id}'")

        try:
            identity = Identity.objects.create(
                group=group,
                type=body.type,
                username=body.username,
                value=body.value
            )
        except IntegrityError as e:
            return BadRequest(message=e.__cause__)

        return ModelResponse(identity)