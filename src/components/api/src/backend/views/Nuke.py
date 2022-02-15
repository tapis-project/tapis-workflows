from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.services.CredentialService import CredentialService
from backend.settings import DJANGO_TAPIS_TOKEN_HEADER
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
            if model.__class__.__name__ != "Credential":
                model.objects.all().delete()
                continue
            credentials = Credential.objects.all()

            cred_service = CredentialService(request.META[DJANGO_TAPIS_TOKEN_HEADER])
            for credential in credentials:
                cred_service.delete(credential.sk_id)

        return BaseResponse(message="Boom")