from django.db import IntegrityError

from backend.models import Alias, CONTEXT_TYPES
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.responses.errors import BadRequest
from backend.views.http.requests import AliasCreateRequest
from backend.services.GroupService import service


ALIAS_TYPES = [ alias_type[0] for alias_type in CONTEXT_TYPES ]

class Aliases(RestrictedAPIView):
    def get(self, request):
        aliases = Alias.objects.all()

        return ModelListResponse(aliases)

    def post(self, request):
        # Validate the request body
        self.prepare(AliasCreateRequest)

        # Return the failure view instance if validation failed
        if not self.prepared_request.is_valid:
            return self.prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = self.prepared_request.body

        # Determine if a user is creating an alias for themselves, or
        # on behalf of another user as a group owner
        on_behalf_of = body.username == request.username

        # Fetch the group
        group = service.get(body.group_id)

        # Return bad request if group does not exist
        if group is None:
            return BadRequest(f"Group with id '{body.group_id}' does not exist")

        # Return bad request if invalid alias type
        if body.type not in ALIAS_TYPES:
            return BadRequest(f"Invalid type for alias. Recieved: {body.type} - Expected one of the following: {ALIAS_TYPES}")

        # Return bad request is user is unable to create an alias themselves in this group
        # or for another user if they are not the group owner
        if (
            not service.user_in_group(body.username, group.id)
            or (on_behalf_of and not service.user_owns_group(request.username, body.group_id))
        ):
            return BadRequest(message=f"You cannot create an alias for user '{body.username}' for group '{body.group_id}'")

        try:
            alias = Alias.objects.create(
                group=group,
                type=body.type,
                username=body.username,
                value=body.value
            )
        except IntegrityError as e:
            return BadRequest(message=e.__cause__)

        return ModelResponse(alias)