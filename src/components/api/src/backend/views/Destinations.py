from backend.models import Destination
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.models import ModelListResponse


class Destinations(RestrictedAPIView):
    def get(self, request):
        destination = Destination.objects.all()

        return ModelListResponse(destination)