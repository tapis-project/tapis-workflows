from backend.models import Action
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.models import ModelListResponse


class Actions(RestrictedAPIView):
    def get(self, request):
        actions = Action.objects.all()

        return ModelListResponse(result=actions)