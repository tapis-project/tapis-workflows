from django.db import DatabaseError, IntegrityError, OperationalError
from django.forms import model_to_dict

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import APIEvent
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.responses.errors import ServerError, MethodNotAllowed, Forbidden, NotFound, BadRequest
from backend.utils.parse_directives import parse_directives as parse
from backend.services import pipeline_dispatcher, group_service
from backend.services.CredentialsService import CredentialsService
from backend.models import Event, Pipeline


class Events(RestrictedAPIView):
    def post(self, request, pipeline_id, *args, **kwargs):
        prepared_request = self.prepare(APIEvent)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

        # Find a pipeline that matches the request data
        pipeline = Pipeline.objects.filter(id=pipeline_id).prefetch_related(
            "actions",
            "actions__context",
            "actions__context__credentials",
            "actions__destination",
            "actions__destination__credentials"
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
                identity=None,
            )
        except (IntegrityError, OperationalError, DatabaseError) as e:
            return ServerError(message=e.__cause__)

        # Return the event if there is no pipeline matching the event
        if pipeline is None:
            return ModelResponse(event)

        # Get the pipeline actions, their contexts, destinations, and respective
        # credentials and generate a piplines_service_request
        actions = pipeline.actions.all()
        actions_result = []
        
        for action in actions:
            # Build action request
            action_request = getattr(self, f"_{action.type}")(action)
            actions_result.append(action_request)

        # Convert pipleline to a dict and build the pipeline_dispatch_request
        pipeline_dispatch_request = {}
        pipeline_dispatch_request["event"] = model_to_dict(event)
        pipeline_dispatch_request["pipeline"] = model_to_dict(pipeline)
        pipeline_dispatch_request["pipeline"]["actions"] = actions_result

        # Parse the directives from the commit message
        directives = {}
        if body.directives is not None and len(body.directives) > 0:
            directive_str = f"[{'|'.join([d for d in body.directives])}]"
            directives = parse(directive_str)

        pipeline_dispatch_request["directives"] = directives

        # Send the pipelines service a service request
        pipeline_dispatcher.dispatch(pipeline_dispatch_request)

        # Respond with the pipeline_context and build data
        # return BaseResponse(result=pipeline_dispatch_request)
        return ModelResponse(event)

    def get(self, request, pipeline_id, event_uuid=None):
        # Get the pipline
        pipeline = Pipeline.objects.filter(id=pipeline_id).first()

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

    def _image_build(self, action):
        action_request = model_to_dict(action)

        # Initialized the credentials service
        cred_service = CredentialsService()

        action_request["context"] = model_to_dict(action.context)
        if action.context.credentials is not None:
            action_request["context"]["credentials"] = model_to_dict(action.context.credentials)

            # Get the context credentials data
            context_cred_data = cred_service.get_secret(action.context.credentials.sk_id)
            action_request["context"]["credentials"]["data"] = context_cred_data

        action_request["destination"] = model_to_dict(action.destination)
        action_request["destination"]["credentials"] = model_to_dict(action.destination.credentials)

        # Get the context credentials data
        destination_cred_data = cred_service.get_secret(action.destination.credentials.sk_id)
        action_request["destination"]["credentials"]["data"] = destination_cred_data

        return action_request

    def _webhook_notification(self, action):
        action_request = model_to_dict(action)
        return action_request

    def _container_run(self, action):
        action_request = model_to_dict(action)
        return action_request