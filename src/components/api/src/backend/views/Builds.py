from backend.models import Build
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.models import ModelListResponse


class Builds(RestrictedAPIView):
    def get(self, request):
        builds = Build.objects.all()

        return ModelListResponse(builds)