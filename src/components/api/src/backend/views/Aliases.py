from django.http import HttpResponse

from backend.views.APIView import APIView
from backend.models import Alias


class Aliases(APIView):

    def post(self, request):

        return HttpResponse(f"{type(self).__name__}: {inspect.stack()[0][3]}")