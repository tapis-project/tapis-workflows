from backend.models import Policy
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.models import ModelListResponse


class Policies(RestrictedAPIView):
    def get(self, request):
        policies = Policy.objects.all()

        return ModelListResponse(policies)