from django.db import DatabaseError, IntegrityError, OperationalError
from django.forms import model_to_dict

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import APIEvent
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.responses.errors import ServerError
from backend.utils.parse_directives import parse_directives as parse
from backend.services import cred_service, pipeline_dispatcher, group_service
from backend.models import Identity, Event, Pipeline
from backend.views.http.responses.BaseResponse import BaseResponse

class APIEvents(RestrictedAPIView):
    def get(self, request):
        return ModelListResponse(Event.objects.all())

    def post(self, request, pipeline_id):
        prepared_request = self.prepare(APIEvent)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

        # Find a pipeline that matches the request data
        pipeline = Pipeline.objects.filter(id=pipeline_id).prefetch_related(
            "actions",
            "actions__context",
            "actions__context__credential",
            "actions__destination",
            "actions__destination__credential"
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

    def _image_build(self, action):
        action_request = model_to_dict(action)

        action_request["context"] = model_to_dict(action.context)
        if action.context.credential is not None:
            action_request["context"]["credential"] = model_to_dict(action.context.credential)

            # Get the context credential data
            context_cred_data = cred_service.get_secret(action.context.credential.sk_id)
            action_request["context"]["credential"]["data"] = context_cred_data

        action_request["destination"] = model_to_dict(action.destination)
        action_request["destination"]["credential"] = model_to_dict(action.destination.credential)

        # Get the context credential data
        destination_cred_data = cred_service.get_secret(action.destination.credential.sk_id)
        action_request["destination"]["credential"]["data"] = destination_cred_data

        return action_request

    def _webhook_notification(self, action):
        action_request = model_to_dict(action)
        return action_request

    def _container_run(self, action):
        action_request = model_to_dict(action)
        return action_request