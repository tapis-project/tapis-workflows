from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.models import Account, Action, Alias, Build, Credential, Context, Destination, Group, GroupUser, Event, Pipeline, Policy

models = [
    Account,
    Action,
    Alias,
    Build,
    Credential,
    Context,
    Destination,
    Group,
    GroupUser,
    Event,
    Pipeline,
    Policy
]

class Nuke(RestrictedAPIView):
    def delete(self, request):
        for model in models:
            model.objects.all().delete()

        return BaseResponse(message="Boom")