from django.http import HttpResponse

from backend.views.APIView import APIView
import inspect


class Actions(APIView):
    def get(self, request):
        return HttpResponse(f"{type(self).__name__}: {inspect.stack()[0][3]}")

    def post(self, request):
        return HttpResponse(f"{type(self).__name__}: {inspect.stack()[0][3]}")

    def put(self, request):
        return HttpResponse(f"{type(self).__name__}: {inspect.stack()[0][3]}")

    def patch(self, request):
        return HttpResponse(f"{type(self).__name__}: {inspect.stack()[0][3]}")

    def delete(self, request):
        return HttpResponse(f"{type(self).__name__}: {inspect.stack()[0][3]}")