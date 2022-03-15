from uuid import uuid4

from django.db import IntegrityError, OperationalError

from backend.models import Action, Context, Destination
from backend.models import ACTION_TYPE_WEBHOOK_NOTIFICATION, ACTION_TYPE_IMAGE_BUILD, ACTION_TYPE_CONTAINER_RUN
from backend.views.http.requests import WebhookAction, ImageBuildAction, ContainerRunAction
from backend.services.CredentialService import service as cred_service


ACTION_REQUEST_MAPPING = {
    ACTION_TYPE_IMAGE_BUILD: ImageBuildAction,
    ACTION_TYPE_WEBHOOK_NOTIFICATION: WebhookAction,
    ACTION_TYPE_CONTAINER_RUN: ContainerRunAction
}

ACTION_REQUEST_TYPES = list(ACTION_REQUEST_MAPPING.keys())

class ActionService:

    def create(self, pipeline, group, request):
        # Create the context
        context = None
        if request.context is not None:
            # Persist the credentials for the context and destination in SK and
            # and save a ref to it in the database
            # Create the credential for the context if one is specified
            context_cred = None
            if hasattr(request.context, "credential") and request.context.credential is not None:
                context_cred_data = {}
                for key, value in dict(request.context.credential).items():
                    if value is not None:
                        context_cred_data[key] = getattr(request.context.credential, key)
                
                try:
                    context_cred = cred_service.save(
                        f"{group.id}+{pipeline.id}+context-{uuid4()}",
                        group,
                        context_cred_data
                    )
                except (IntegrityError, OperationalError) as e:
                    raise e

            try:
                context = Context.objects.create(
                    branch=request.context.branch,
                    credential=context_cred,
                    dockerfile_path=request.context.dockerfile_path,
                    sub_path=request.context.sub_path,
                    type=request.context.type,
                    url=request.context.url,
                    visibility=request.context.visibility
                )
            except (IntegrityError, OperationalError) as e:
                cred_service.delete(context_cred.sk_id)
                raise e

        destination = None
        if request.destination is not None:
            # Create the credential for the destination (should always be specified)
            destination_cred_data = {}
            for key, value in dict(request.destination.credential).items():
                if value is not None:
                    destination_cred_data[key] = getattr(request.destination.credential, key)
            try:
                destination_cred = cred_service.save(
                    f"{group.id}+{pipeline.id}+destination-{uuid4}",
                    group,
                    destination_cred_data
                )
            except (IntegrityError, OperationalError) as e:
                cred_service.delete(context_cred.sk_id)
                context.delete()
                raise e

            # Create the destination
            try:
                destination = Destination.objects.create(
                    credential=destination_cred,
                    tag=request.destination.tag,
                    type=request.destination.type,
                    url=request.destination.url
                )
            except (IntegrityError, OperationalError) as e:
                cred_service.delete(context_cred.sk_id)
                context.delete()
                cred_service.delete(destination_cred.sk_id)
                raise e

        # Create action
        try:
            action = Action.objects.create(
                auth=request.auth,
                builder=request.builder,
                cache=request.cache,
                context=context,
                data=request.data,
                description=request.description,
                destination=destination,
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

        # Validate graph here

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
