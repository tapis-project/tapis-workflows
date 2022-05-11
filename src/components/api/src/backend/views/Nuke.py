from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.services import cred_service
from backend.models import Action, Identity, Build, Credentials, Context, Destination, Group, GroupUser, Event, Pipeline

models = [
    Action,
    Identity,
    Build,
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
        for model in models:
            if model.__class__.__name__ != "Credentials":
                model.objects.all().delete()
                continue
            
            credentials_list = Credentials.objects.all()

            for credentials in credentials_list:
                cred_service.delete(credentials.sk_id)

        return BaseResponse(message="Boom")