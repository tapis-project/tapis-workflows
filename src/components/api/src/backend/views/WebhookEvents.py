from django.db import IntegrityError
from django.forms import model_to_dict

from backend.views.APIView import APIView
from backend.views.http.requests import WebhookEvent
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.responses.errors import ServerError
from backend.utils.parse_directives import parse_directives as parse
from backend.services.CredentialsService import CredentialsService
from backend.services import pipeline_dispatcher
from backend.models import Identity, Event, Pipeline, Group
from backend.views.http.responses.BaseResponse import BaseResponse

class WebhookEvents(APIView):
    def post(self, request, pipeline_id):
        prepared_request = self.prepare(WebhookEvent)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

        # Find a pipeline that matches the request data
        pipeline = Pipeline.objects.filter(id=pipeline_id).prefetch_related(
            "group",
            "actions",
            "actions__context",
            "actions__context__credentials",
            "actions__context__identity",
            "actions__destination",
            "actions__destination__credentials",
            "actions__destination__identity",
        ).first()

        message = "No Pipeline found with details that match this event"
        if pipeline != None:
            message = f"Successfully triggered pipeline ({pipeline.id})"
            
        # Persist the event in the database
        try:
            event = Event.objects.create(
                branch=body.branch,
                commit=body.commit,
                commit_sha=body.commit_sha,
                context_url=body.context_url,
                message=message,
                pipeline=pipeline,
                source=body.source,
                username=body.username
            )
        except IntegrityError as e:
            return ServerError(message=e.__cause__)

        # Return the event if there is no pipeline matching the event
        if pipeline is None:
            return ModelResponse(event)

        # Get the group for this pipelines
        group = pipeline.group

        # Get the pipeline actions, their contexts, destinations, and respective
        # credentials and generate a piplines_service_request
        actions = pipeline.actions.all()
        
        actions_request = []
        for action in actions:
            # Build action result
            action_request = getattr(self, f"_{action.type}")(action)
            actions_request.append(action_request)

        # Convert pipleline to a dict and build the pipeline_dispatch_request
        pipeline_dispatch_request = {}
        pipeline_dispatch_request["group"] = model_to_dict(group)
        pipeline_dispatch_request["event"] = model_to_dict(event)
        pipeline_dispatch_request["pipeline"] = model_to_dict(pipeline)
        pipeline_dispatch_request["pipeline"]["actions"] = actions_request

        # Parse the directives from the commit message
        directives = parse(body.commit)
        pipeline_dispatch_request["directives"] = directives

        # Send the pipelines service a service request
        pipeline_dispatcher.dispatch(pipeline_dispatch_request)

        # Respond with the pipeline_context and build data
        # return BaseResponse(result=pipeline_dispatch_request)
        return ModelResponse(event)

    def _image_build(self, action):
        action_request = model_to_dict(action)

        cred_service = CredentialsService()

        action_request["context"] = model_to_dict(action.context)

        # Resolve which context credentials to use if any provided
        context_creds = None
        if action.context.credentials != None:
            context_creds = action.context.credentials
        
        # Identity takes precedence over credentials placed directly in
        # the context
        if action.context.identity != None:
            context_creds = action.context.identity.credentials

        action_request["context"]["credentials"] = None
        if context_creds != None:
            action_request["context"]["credentials"] = model_to_dict(context_creds)

            # Get the context credentials data
            context_cred_data = cred_service.get_secret(context_creds.sk_id)
            action_request["context"]["credentials"]["data"] = context_cred_data

        # Destination credentials
        action_request["destination"] = model_to_dict(action.destination)

        destination_creds = None
        if action.destination.credentials != None:
            destination_creds = action.destination.credentials

        if action.destination.identity != None:
            destination_creds = action.destination.identity.credentials

        if destination_creds != None:
            action_request["destination"]["credentials"] = model_to_dict(destination_creds)

            # Get the context credentials data
            destination_cred_data = cred_service.get_secret(destination_creds.sk_id)
            action_request["destination"]["credentials"]["data"] = destination_cred_data

        return action_request

    def _webhook_notification(self, action):
        action_request = model_to_dict(action)
        return action_request

    def _container_run(self, action):
        action_request = model_to_dict(action)
        return action_request