from django.db import IntegrityError

from backend.models import Action
from backend.models import ACTION_TYPE_WEBHOOK_NOTIFICATION, ACTION_TYPE_IMAGE_BUILD, ACTION_TYPE_CONTAINER_RUN
from backend.views.http.requests import WebhookActionCreateRequest, ImageBuildActionCreateRequest, ContainerRunActionCreateRequest


ACTION_REQUEST_MAPPING = {
    ACTION_TYPE_IMAGE_BUILD: ImageBuildActionCreateRequest,
    ACTION_TYPE_WEBHOOK_NOTIFICATION: WebhookActionCreateRequest,
    ACTION_TYPE_CONTAINER_RUN: ContainerRunActionCreateRequest
}

ACTION_REQUEST_TYPES = list(ACTION_REQUEST_MAPPING.keys())

class ActionService:
    def create(self, pipeline, request):
        # Create 'build' action
        try:
            action = Action.objects.create(
                builder=pipeline.builder,
                description=request.description if hasattr(request, "description") else None,
                http_method=request.http_method,
                name=request.name,
                pipeline=pipeline,
                stage=request.stage,
                type=request.type,
                url=request.url
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
