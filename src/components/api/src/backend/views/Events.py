from django.db import IntegrityError
from django.forms import model_to_dict

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import EventCreateRequest
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.errors import ServerError
from backend.helpers.parse_commit import parse_commit as parse
from backend.services.PipelineService import pipeline_service
from backend.services.CredentialService import cred_service
from backend.models import Event, Pipeline, GroupUser


class Events(RestrictedAPIView):
    def get(self, request):
        return ModelListResponse(Event.objects.all())

    def post(self, request, **_):
        prepared_request = self.prepare(EventCreateRequest)

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
            # Get all the groups the user belongs to
            group_users = GroupUser.objects.filter(username=body.username)
            group_ids = [ group_user.group_id for group_user in group_users ]


            # TODO Resolve aliases for username
            # Check that the user belongs to the group that is attached
            # to this pipline
            message = f"Successfully triggered pipeline ({pipeline.id})"
            if pipeline.group_id not in group_ids:
                message = f"Failed to trigger pipline ({pipeline.id}): User {body.username} does not belong to the group attached to the pipline"

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

        # Get the pipeline actions, their contexts, destinations, and respective
        # credentials and generate a piplines_service_request
        actions = pipeline.actions.all()
        actions_result = []
        for action in actions:
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

            actions_result.append(action_result)

        # Convert pipleline to a dict and build the pipelines_service_request
        pipelines_service_request = {}
        pipelines_service_request["event"] = model_to_dict(event)
        pipelines_service_request["pipeline"] = model_to_dict(pipeline)
        pipelines_service_request["pipeline"]["actions"] = actions_result

        # Parse the directives from the commit message
        directives = parse(body.commit)
        pipelines_service_request["directives"] = directives

        # Conver the uuid object of the event
        # Send the pipelines service a service request
        pipeline_service.start(pipelines_service_request)

        # Create the build object with status QUEUED
        # TODO create build object

        # Respond with the pipeline_context and build data
        # return BaseResponse(result=pipelines_service_request)
        return ModelResponse(event)