from django.http import HttpResponse
from django.views import View

from backend.helpers.parse_commit import parse_commit as parse
from backend.services.BuildService import build_service
# TODO Remove
from backend.fixtures.pipeline_context import pipeline_context
import json

class Builds(View):

    def get(self, request):
        return self.post(request)
    
    def post(self, request):
        # Fetch the deployment and related daata that matches incoming request
        # TODO fetch build context data
        directives = parse(pipeline_context["event"]["commit"])
        pipeline_context["directives"] = directives

        build = build_service.start(pipeline_context)

        # Create the build object with status QUEUED
        # TODO create build object

        # Respond with the pipeline_context and build data
        return HttpResponse(json.dumps(build))

    def put(self, request):
        return HttpResponse(f"put")

    def patch(self, request):
        return HttpResponse(f"patch")

    def delete(self, request):
        return HttpResponse(f"delete")