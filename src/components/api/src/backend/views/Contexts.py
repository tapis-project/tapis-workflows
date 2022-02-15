from backend.models import Context
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.models import ModelListResponse


class Contexts(RestrictedAPIView):
    def get(self, request):
        contexts = Context.objects.all()

        return ModelListResponse(contexts)