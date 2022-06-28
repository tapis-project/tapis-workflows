from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.services import CredentialsService
from backend.models import Action, Identity, Credentials, Context, Destination, Group, GroupUser, Event, Pipeline

models = [
    Action,
    Identity,
    Credentials,
    Context,
    Destination,
    Group,
    GroupUser,
    Event,
    Pipeline
]

class Nuke(RestrictedAPIView):
    def delete(self, request):
        cred_service = CredentialsService()
        for model in models:
            if model.__class__.__name__ != "Credentials":
                model.objects.all().delete()
                continue
            
            credentials_list = Credentials.objects.all()

            for credentials in credentials_list:
                cred_service.delete(credentials.sk_id)

        return BaseResponse(message="Boom")