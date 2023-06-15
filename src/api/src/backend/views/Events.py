from django.db import DatabaseError, IntegrityError, OperationalError

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import APIEvent
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.responses.errors import (
    ServerError as ServerErrorResp,
    MethodNotAllowed,
    Forbidden,
    NotFound,
    BadRequest
)
from backend.errors.api import ServerError
from backend.helpers.PipelineDispatchRequestBuilder import PipelineDispatchRequestBuilder
from backend.services.PipelineDispatcher import service as pipeline_dispatcher
from backend.services.GroupService import service as group_service
from backend.services.SecretService import service as secret_service
from backend.models import Event, Pipeline


request_builder = PipelineDispatchRequestBuilder(secret_service)

class Events(RestrictedAPIView):
    def post(self, request, group_id, pipeline_id, *_, **__):
        prepared_request = self.prepare(APIEvent)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

        # Get the group
        group = group_service.get(group_id, request.tenant_id)
        if group == None:
            return NotFound(f"No group found with id '{group_id}'")

        # Check that the user belongs to the group
        if not group_service.user_in_group(request.username, group_id, request.tenant_id):
            return Forbidden(message="You do not have access to this group")

        # Find a pipeline that matches the request data
        pipeline = Pipeline.objects.filter(
            id=pipeline_id,
            group=group
        ).prefetch_related(
            "group",
            "archives",
            "archives__archive",
            "tasks",
            "tasks__context",
            "tasks__context__credentials",
            "tasks__context__identity",
            "tasks__destination",
            "tasks__destination__credentials",
            "tasks__destination__identity",
        ).first()

        message = "No Pipeline found with details that match this event"
        if pipeline != None:
            # Check that the user belongs to the group that is attached
            # to this pipline
            message = f"Successfully triggered pipeline ({pipeline.id})"

        # Persist the event in the database
        try:
            event = Event.objects.create(
                message=message,
                pipeline=pipeline,
                source="api",
                username=request.username,
            )
        except (IntegrityError, OperationalError, DatabaseError) as e:
            return ServerErrorResp(message=e.__cause__)

        # Return the event if there is no pipeline matching the event
        if pipeline == None:
            return ModelResponse(event)


        try:
            # Build the pipeline dispatch request
            pipeline_dispatch_request = request_builder.build(
                request.base_url,
                group,
                pipeline,
                event,
                directives=body.directives,
                params=body.params
            )
            
            # Dispatch the request
            pipeline_dispatcher.dispatch(pipeline_dispatch_request, pipeline)
        except ServerError as e:
            return ServerErrorResp(message=str(e))
        except Exception as e:
            print(str(e))
            return ServerErrorResp(message=str(e))

        # Respond with the event
        return ModelResponse(event)

    def get(self, request, group_id, pipeline_id, event_uuid=None):
        # Get the group
        group = group_service.get(group_id, request.tenant_id)
        if group == None:
            return NotFound(f"No group found with id '{group_id}'")

        # Check that the user belongs to the group
        if not group_service.user_in_group(request.username, group_id, request.tenant_id):
            return Forbidden(message="You do not have access to this group")

        # Get the pipline
        pipeline = Pipeline.objects.filter(
            group=group,
            id=pipeline_id
        ).first()

        # Return if BadRequest if no pipeline found
        if pipeline == None:
            return BadRequest(f"Pipline '{pipeline_id}' does not exist")

        # Return a list of events if uuid is not specified
        if event_uuid == None:
            return self.list(pipeline)

        event = Event.objects.filter(uuid=event_uuid).first()

        if event == None:
            return NotFound(f"Event with uuid '{event_uuid}' not found in pipeline '{pipeline_id}'")

        return ModelResponse(event)

    def list(self, pipeline):    
        events = Event.objects.filter(pipeline=pipeline)
        return ModelListResponse(events)

    def put(self, *args, **kwargs):
        return MethodNotAllowed(message="Events cannot be updated")

    def patch(self, *args, **kwargs):
        return MethodNotAllowed(message="Events cannot be updated")

    def delete(self, *args, **kwargs):
        return MethodNotAllowed(message="Events cannot be deleted")