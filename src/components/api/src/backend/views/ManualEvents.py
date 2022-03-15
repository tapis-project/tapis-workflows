from django.db import IntegrityError
from django.forms import model_to_dict

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import WebhookEvent
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.responses.errors import ServerError
from backend.helpers.parse_commit import parse_commit as parse
from backend.services.PipelineDispatcher import pipeline_dispatcher
from backend.services import cred_service
from backend.models import Identity, Event, Pipeline
from backend.views.http.responses.BaseResponse import BaseResponse

class ManualEvents(RestrictedAPIView):
    def get(self, request):
        return ModelListResponse(Event.objects.all())

    def post(self, request, **_):
        prepared_request = self.prepare(WebhookEvent)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

        # Find a pipeline that matches the request data
        pipeline = Pipeline.objects.filter(
            branch=body.branch,
            context_type=body.source,
            context_url=body.context_url
        ).prefetch_related(
            "actions",
            "actions__context",
            "actions__context__credential",
            "actions__destination",
            "actions__destination__credential"
        ).first()

        message = "No Pipeline found with details that match this event"
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
                message = f"Failed to trigger pipline ({pipeline.id}): {body.type} identity '{body.username}' does not have access to this pipeline"

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
                username=identity.username if identity is not None else None,
                identity=identity
            )
        except IntegrityError as e:
            return ServerError(message=e.__cause__)

        # Return the event if there is no pipeline matching the event
        if pipeline is None and identity is not None:
            return ModelResponse(event)

        # Get the pipeline actions, their contexts, destinations, and respective
        # credentials and generate a piplines_service_request
        actions = pipeline.actions.all()
        actions_result = []
        
        for action in actions:
            # Build action result
            action_result = getattr(self, f"_{action.type}")(action)
            actions_result.append(action_result)

        # Convert pipleline to a dict and build the pipleine_dispatch_request
        pipleine_dispatch_request = {}
        pipleine_dispatch_request["event"] = model_to_dict(event)
        pipleine_dispatch_request["pipeline"] = model_to_dict(pipeline)
        pipleine_dispatch_request["pipeline"]["actions"] = actions_result

        # Parse the directives from the commit message
        directives = parse(body.commit)
        pipleine_dispatch_request["directives"] = directives

        # Conver the uuid object of the event
        # Send the pipelines service a service request
        pipeline_dispatcher.dispatch(pipleine_dispatch_request)

        # Respond with the pipeline_context and build data
        # return BaseResponse(result=pipleine_dispatch_request)
        return ModelResponse(event)

    def _image_build(self, action):
        action_result = model_to_dict(action)

        action_result["context"] = model_to_dict(action.context)
        if action.context.credential is not None:
            action_result["context"]["credential"] = model_to_dict(action.context.credential)

            # Get the context credential data
            context_cred_data = cred_service.get_secret(action.context.credential.sk_id)
            action_result["context"]["credential"]["data"] = context_cred_data

        action_result["destination"] = model_to_dict(action.destination)
        action_result["destination"]["credential"] = model_to_dict(action.destination.credential)

        # Get the context credential data
        destination_cred_data = cred_service.get_secret(action.destination.credential.sk_id)
        action_result["destination"]["credential"]["data"] = destination_cred_data

        return action_result

    def _webhook_notification(self, action):
        action_result = model_to_dict(action)
        return action_result

    def _container_run(self, action):
        action_result = model_to_dict(action)
        return action_result