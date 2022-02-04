from django.http import HttpResponse
from django.views import View

class Builds(View):
    
    def get(self, request):
        return HttpResponse("get")
    
    def post(self, request):
        return HttpResponse(f"post")

    def put(self, request):
        return HttpResponse(f"put")

    def patch(self, request):
        return HttpResponse(f"patch")

    def delete(self, request):
        return HttpResponse(f"delete")