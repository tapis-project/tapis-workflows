from django.http import HttpResponse
from django.views import View
import inspect

from backend.helpers.parse_commit import parse_commit as parse
from backend.services.BuildService import build_service
# TODO Remove
from backend.fixtures.pipeline_context import pipeline_context
import json


class Events(View):
    def get(self, request):
        self.post(request)

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
        return HttpResponse(f"{type(self).__name__}: {inspect.stack()[0][3]}")

    def patch(self, request):
        return HttpResponse(f"{type(self).__name__}: {inspect.stack()[0][3]}")

    def delete(self, request):
        return HttpResponse(f"{type(self).__name__}: {inspect.stack()[0][3]}")