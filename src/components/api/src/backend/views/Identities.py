from django.db import IntegrityError

from backend.models import Identity, CONTEXT_TYPES
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.responses.errors import BadRequest
from backend.views.http.requests import IdentityCreateRequest
from backend.services.GroupService import service


IDENTITY_TYPES = [ identity_type[0] for identity_type in CONTEXT_TYPES ]

class Identities(RestrictedAPIView):
    def get(self, request, group_id):

        # Fetch the group
        group = service.get(group_id)

        # Return bad request if group does not exist
        if group is None:
            return BadRequest(f"Group with id '{group_id}' does not exist")

        # Return bad request is user is not in group
        if not service.user_in_group(request.username, group.id):
            return BadRequest(message=f"You cannot view identities for group '{group_id}'")

        identities = Identity.objects.filter(group_id=group_id)

        return ModelListResponse(identities)

    def post(self, request, group_id, *args, **kwargs):
        # Validate the request body
        self.prepare(IdentityCreateRequest)

        # Return the failure view instance if validation failed
        if not self.prepared_request.is_valid:
            return self.prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = self.prepared_request.body

        # Fetch the group
        group = service.get(group_id)

        # Return bad request if group does not exist
        if group is None:
            return BadRequest(f"Group with id '{group_id}' does not exist")

        # Return bad request if invalid identity type
        if body.type not in IDENTITY_TYPES:
            return BadRequest(f"Invalid type for identity. Recieved: {body.type} - Expected one of the following: {IDENTITY_TYPES}")

        # Return bad request is user does not belong to group
        if service.user_in_group(request.username, group.id) == False:
            return BadRequest(message=f"You cannot create an identity for user '{request.username}' for group '{group_id}'")

        try:
            identity = Identity.objects.create(
                group=group,
                type=body.type,
                owner=request.username,
                value=body.value
            )
        except IntegrityError as e:
            return BadRequest(message=e.__cause__)

        return ModelResponse(identity)