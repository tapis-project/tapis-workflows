from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.services.CredentialService import cred_service
from backend.models import Action, Identity, Build, Credential, Context, Destination, Group, GroupUser, Event, Pipeline, Policy

models = [
    Action,
    Identity,
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

            for credential in credentials:
                cred_service.delete(credential.sk_id)

        return BaseResponse(message="Boom")