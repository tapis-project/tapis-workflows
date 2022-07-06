from django.db import DatabaseError, IntegrityError, OperationalError

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import APIEvent
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.responses.errors import (
    ServerError,
    MethodNotAllowed,
    Forbidden,
    NotFound,
    BadRequest,
    UnprocessableEntity
)
from backend.helpers.PipelineDispatchRequestBuilder import PipelineDispatchRequestBuilder
from backend.services.PipelineDispatcher import service as pipeline_dispatcher
from backend.services.GroupService import service as group_service
from backend.services.CredentialsService import service as cred_service
from backend.models import Event, Pipeline


request_builder = PipelineDispatchRequestBuilder(cred_service)

class Events(RestrictedAPIView):
    def post(self, request, group_id, pipeline_id, *_, **__):
        prepared_request = self.prepare(APIEvent)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

        # Get the group for this request
        group = group_service.get(group_id)

        # Return Event if group does not exist
        if group == None:
            return UnprocessableEntity(message=f"Group '{group_id}' does not exist")

        if not group_service.user_in_group(request.username, group.id):
            return Forbidden(f"You do not have access to group '{group_id}'")

        # Find a pipeline that matches the request data
        pipeline = Pipeline.objects.filter(
            id=pipeline_id,
            group_id=group_id
        ).prefetch_related(
            "group",
            "archives",
            "archives__archive",
            "actions",
            "actions__context",
            "actions__context__credentials",
            "actions__context__identity",
            "actions__destination",
            "actions__destination__credentials",
            "actions__destination__identity",
        ).first()

        message = "No Pipeline found with details that match this event"
        if pipeline is not None:
            # Check that the user belongs to the group that is attached
            # to this pipline
            message = f"Successfully triggered pipeline ({pipeline.id})"
            if not group_service.user_in_group(request.username, pipeline.group_id):
                message = f"Failed to trigger pipline ({pipeline.id}): '{request.username}' does not have access to this pipeline"

        # Persist the event in the database
        try:
            event = Event.objects.create(
                message=message,
                pipeline=pipeline,
                source="api",
                username=request.username,
            )
        except (IntegrityError, OperationalError, DatabaseError) as e:
            return ServerError(message=e.__cause__)

        # Return the event if there is no pipeline matching the event
        if pipeline is None:
            return ModelResponse(event)

        # Build the pipeline dispatch request
        pipeline_dispatch_request = request_builder.build(
            group,
            pipeline,
            event,
            directives=body.directives
        )

        # Dispatch the request
        pipeline_dispatcher.dispatch(pipeline_dispatch_request)

        # Respond with the event
        return ModelResponse(event)

    def get(self, request, group_id, pipeline_id, event_uuid=None):
        # Get the pipline
        pipeline = Pipeline.objects.filter(
            group_id=group_id,
            id=pipeline_id
        ).first()

        # Return if BadRequest if no pipeline found
        if pipeline is None:
            return BadRequest(f"Pipline '{pipeline_id}' does not exist")

        # Check that the user belongs to the group that is attached
        # to this pipline
        if not group_service.user_in_group(request.username, pipeline.group_id):
            return Forbidden(message="You cannot view events for this pipeline")

        # Return a list of events if uuid is not specified
        if event_uuid is None:
            return self.list(pipeline_id)

        event = Event.objects.filter(uuid=event_uuid).first()

        if event is None:
            return NotFound(f"Event with uuid '{event_uuid}' not found in pipeline '{pipeline_id}'")

        return ModelResponse(event)

    def list(self, pipeline_id):    
        events = Event.objects.filter(pipeline=pipeline_id)
        return ModelListResponse(events)

    def put(self, *args, **kwargs):
        return MethodNotAllowed(message="Events cannot be updated")

    def patch(self, *args, **kwargs):
        return MethodNotAllowed(message="Events cannot be updated")

    def delete(self, *args, **kwargs):
        return MethodNotAllowed(message="Events cannot be deleted")