import json

from django.forms.models import model_to_dict

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.responses.models import ModelResponseOr404, ModelResponse, ModelListResponse
from backend.views.responses.http_errors import ServerError, Conflict
from backend.models import Group


class Groups(RestrictedAPIView):
    def get(self, _, name=None):
        # Get a list of the groups if name is not set
        if name is None:
            return ModelListResponse(Group.objects.all())

        # Return the group by the name provided in the path params
        return ModelResponseOr404(
            Group.objects.filter(name=name).first())

    def post(self, request, **_):
        validation = self.validate_request_body(
            request.body, ["name"])

        if not validation.success:
            return validation.failure_view

        body = validation.body

        # Check that name of the group is unique
        if Group.objects.filter(name=body["name"]).exists():
            return Conflict(f"A Group already exists with the name '{body['name']}'")

        try:
            group = Group.objects.create(name=body["name"], owner=request.username)
        except Exception as e:
            return ServerError(message=str(e))
        
        return ModelResponse(group)

    def patch(self, request, name=None):
        pass
