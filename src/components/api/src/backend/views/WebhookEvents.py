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
            "actions__destination",
            "actions__destination__credentials"
        ).first()

        message = "No Pipeline found with details that match this event"
        identity = None
        if pipeline is not None:
            # Get the user and group info for the triggering user
            identity = Identity.objects.filter(
                group_id=pipeline.group_id,
                type=body.source,
                value=body.username
            ).first()


            # TODO Resolve indentities for username
            # Check that the user belongs to the group that is attached
            # to this pipline
            message = f"Successfully triggered pipeline ({pipeline.id})"
            if identity is None:
                message = f"Failed to trigger pipeline ({pipeline.id}): {body.source} identity '{body.username}' does not have access to this pipeline"

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
                username=identity.owner if identity is not None else f"{body.source}:{body.username}",
                identity=identity
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
        actions_result = []
        
        for action in actions:
            # Build action result
            action_result = getattr(self, f"_{action.type}")(action)
            actions_result.append(action_result)

        # Convert pipleline to a dict and build the pipeline_dispatch_request
        pipeline_dispatch_request = {}
        pipeline_dispatch_request["group"] = model_to_dict(group)
        pipeline_dispatch_request["event"] = model_to_dict(event)
        pipeline_dispatch_request["pipeline"] = model_to_dict(pipeline)
        pipeline_dispatch_request["pipeline"]["actions"] = actions_result

        # Parse the directives from the commit message
        directives = parse(body.commit)
        pipeline_dispatch_request["directives"] = directives

        # Send the pipelines service a service request
        pipeline_dispatcher.dispatch(pipeline_dispatch_request)

        # Respond with the pipeline_context and build data
        # return BaseResponse(result=pipeline_dispatch_request)
        return ModelResponse(event)

    def _image_build(self, action):
        action_result = model_to_dict(action)

        cred_service = CredentialsService()

        action_result["context"] = model_to_dict(action.context)
        if action.context.credentials is not None:
            action_result["context"]["credentials"] = model_to_dict(action.context.credentials)

            # Get the context credentials data
            context_cred_data = cred_service.get_secret(action.context.credentials.sk_id)
            action_result["context"]["credentials"]["data"] = context_cred_data

        action_result["destination"] = model_to_dict(action.destination)
        action_result["destination"]["credentials"] = model_to_dict(action.destination.credentials)

        # Get the context credentials data
        destination_cred_data = cred_service.get_secret(action.destination.credentials.sk_id)
        action_result["destination"]["credentials"]["data"] = destination_cred_data

        return action_result

    def _webhook_notification(self, action):
        action_result = model_to_dict(action)
        return action_result

    def _container_run(self, action):
        action_result = model_to_dict(action)
        return action_result