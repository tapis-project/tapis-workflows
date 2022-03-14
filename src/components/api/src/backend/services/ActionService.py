from django.db import IntegrityError

from backend.models import Action
from backend.models import ACTION_TYPE_WEBHOOK_NOTIFICATION, ACTION_TYPE_IMAGE_BUILD, ACTION_TYPE_CONTAINER_RUN
from backend.views.http.requests import WebhookAction, ImageBuildAction, ContainerRunAction


ACTION_REQUEST_MAPPING = {
    ACTION_TYPE_IMAGE_BUILD: ImageBuildAction,
    ACTION_TYPE_WEBHOOK_NOTIFICATION: WebhookAction,
    ACTION_TYPE_CONTAINER_RUN: ContainerRunAction
}

ACTION_REQUEST_TYPES = list(ACTION_REQUEST_MAPPING.keys())

class ActionService:
    def create(self, pipeline, request):
        # Create 'build' action
        try:
            action = Action.objects.create(
                auth=request.auth,
                builder=request.builder,
                cache=request.cache,
                context=request.context,
                data=request.data,
                description=request.description,
                destination=request.destination,
                headers=request.headers,
                http_method=request.http_method,
                image=request.image,
                input=request.input,
                name=request.name,
                output=request.output,
                query_params=request.query_params,
                pipeline=pipeline,
                type=request.type,
                depends_on=[ dict(item) for item in request.depends_on ],
                retries=request.retries,
                tapis_job_def=request.tapis_job_def,
                tapis_actor_id=request.tapis_actor_id,
                ttl=request.ttl,
                url=request.url,
            )
        except IntegrityError as e:
            raise e

        return action

    def resolve_request_type(self, action_type):
        return ACTION_REQUEST_MAPPING[action_type]

    def is_valid_action_type(self, action_type):
        if action_type in ACTION_REQUEST_MAPPING:
            return True

        return False

    def get_action_request_types(self):
        return ACTION_REQUEST_TYPES

service = ActionService()
