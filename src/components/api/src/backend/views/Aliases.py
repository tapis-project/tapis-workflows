from backend.models import Alias
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.models import ModelListResponse


class Aliases(RestrictedAPIView):
    def get(self, request):
        aliases = Alias.objects.all()

        return ModelListResponse(aliases)