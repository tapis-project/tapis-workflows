from django.http import HttpResponse
from django.views import View
import inspect


class Events(View):
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