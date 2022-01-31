from django.http import HttpResponse
from django.views import View

from backend.helpers.parse_commit import parse_commit as parse
from backend.services.BuildService import build_service
# TODO Remove
from backend.fixtures.build_context import build_context
import json

class Builds(View):

    def get(self, request):
        return self.post(request)
    
    def post(self, request):
        # Fetch the deployment and related daata that matches incoming request
        # TODO fetch build context data
        directives = parse(build_context["event"]["commit"])
        build_context["directives"] = directives

        build = build_service.start(build_context)

        # Create the build object with status QUEUED
        # TODO create build object

        # Respond with the build_context and build data
        return HttpResponse(json.dumps(build))

    def put(self, request):
        return HttpResponse(f"put")

    def patch(self, request):
        return HttpResponse(f"patch")

    def delete(self, request):
        return HttpResponse(f"delete")