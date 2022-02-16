from django.db import IntegrityError
from django.forms import model_to_dict

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import EventCreateRequest
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.errors import ServerError
from backend.helpers.parse_commit import parse_commit as parse
from backend.services.PipelineService import pipeline_service
from backend.models import Event, Pipeline, Group, GroupUser
# TODO Remove
from backend.fixtures.pipeline_context import pipeline_context


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
            context=body.context,
            branch=body.branch,
            context_type=body.source
        ).prefetch_related(
            "actions",
            "actions__context",
            "actions__context__credential",
            "actions__destination",
            "actions__destination__credential"
        ).first()

        message = "Failed to trigger a pipeline: No Pipeline found with details that match this event"
        if pipeline is not None:
            # Get all the groups the user belongs to
            group_users = GroupUser.objects.filter(username=body.username)
            group_ids = [ group_user.group_id for group_user in group_users ]


            # TODO Resolve aliases for username
            # Check that the user belongs to the group that is attached
            # to this pipline
            message = f"Successfully triggered pipeline '{pipeline.id}'"
            if pipeline.group_id not in group_ids:
                message = f"Failed to trigger pipline '{pipeline.id}': User {body.username} does not belong to the group attached to the pipline"

        # # Persist the event in the database
        # try:
        #     event = Event.objects.create(
        #         branch=body.branch,
        #         commit=body.commit,
        #         commit_sha=body.commit_sha,
        #         context=body.context,
        #         message=message,
        #         pipeline=pipeline,
        #         source=body.source,
        #         username=body.username
        #     )
        # except IntegrityError as e:
        #     return ServerError(message=e.__cause__)

        # Get the pipeline actions.
        actions = pipeline.actions.all()
        actions_result = []
        for action in actions:
            action_result = model_to_dict(action)

            action_result["context"] = model_to_dict(action.context)
            if action.context.credential is not None:
                action_result["context"]["credential"] = model_to_dict(action.context.credential)

            action_result["destination"] = model_to_dict(action.destination)
            action_result["destination"]["credential"] = model_to_dict(action.destination.credential)

            actions_result.append(action_result)

        # Convert model into a dict an
        result = model_to_dict(pipeline)
        result["actions"] = actions_result
        
        return BaseResponse(result=result)

        return ModelResponse(pipeline)

        # Fetch the deployment and related data that matches incoming request
        directives = parse(body.commit)
        pipeline_context["directives"] = directives
        # build = pipeline_service.start(pipeline_context)

        # Create the build object with status QUEUED
        # TODO create build object

        # Respond with the pipeline_context and build data
        # return ModelResponse(event)
        return BaseResponse()