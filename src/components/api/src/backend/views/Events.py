import json

from backend.views.responses.BaseResponse import BaseResponse
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.responses.models import ModelListResponse, ModelResponse
from backend.helpers.parse_commit import parse_commit as parse
from backend.services.BuildService import build_service
from backend.models import Event
# TODO Remove
from backend.fixtures.pipeline_context import pipeline_context


class Events(RestrictedAPIView):
    def get(self, request):
        return ModelListResponse(Event.objects.all())

    def post(self, request):
        # Validate the request body
        validation = self.validate_request_body(
            request.body,
            ["branch", "commit", "commit_sha", "source", "username"]
        )

        # Return the failure view instance if validation failed
        if not validation.success:
            return validation.failure_view

        # Get the JSON encoded body from the validation result
        body = validation.body

        # Persist the event in the database
        event = Event.objects.create(**body)

        # Find a pipeline that matches the data data

        # Fetch the deployment and related data that matches incoming request
        directives = parse(body["commit"])
        pipeline_context["directives"] = directives
        # build = build_service.start(pipeline_context)

        # Create the build object with status QUEUED
        # TODO create build object

        # Respond with the pipeline_context and build data
        return ModelResponse(event)