from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import EventCreateRequest
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.helpers.parse_commit import parse_commit as parse
from backend.services.PipelineService import pipeline_service
from backend.models import Event
# TODO Remove
from backend.fixtures.pipeline_context import pipeline_context


class Events(RestrictedAPIView):
    def get(self, request):
        return ModelListResponse(Event.objects.all())

    def post(self, request):
        prepared_request = self.prepare(EventCreateRequest)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

        # Persist the event in the database
        event = Event.objects.create(**body)

        # Find a pipeline that matches the request data

        # Fetch the deployment and related data that matches incoming request
        directives = parse(body["commit"])
        pipeline_context["directives"] = directives
        # build = pipeline_service.start(pipeline_context)

        # Create the build object with status QUEUED
        # TODO create build object

        # Respond with the pipeline_context and build data
        return ModelResponse(event)