from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.services.SecretService import service as secret_service
from backend.models import Task, Identity, Credentials, Context, Destination, Group, GroupUser, Event, Pipeline

models = [
    Task,
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
        for model in models:
            if model.__class__.__name__ != "Credentials":
                model.objects.all().delete()
                continue
            
            credentials_list = Credentials.objects.all()

            for credentials in credentials_list:
                secret_service.delete(credentials.sk_id)

        return BaseResponse(message="Boom")