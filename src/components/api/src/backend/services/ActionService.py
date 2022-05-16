import logging

from django.db import DatabaseError, IntegrityError, OperationalError

from backend.models import Action, Context, Destination, Identity
from backend.models import ACTION_TYPE_WEBHOOK_NOTIFICATION, ACTION_TYPE_IMAGE_BUILD, ACTION_TYPE_CONTAINER_RUN, ACTION_TYPE_TAPIS_JOB, ACTION_TYPE_TAPIS_ACTOR
from backend.views.http.requests import WebhookAction, ImageBuildAction, ContainerRunAction, TapisJobAction
from backend.services.CredentialsService import CredentialsService
from backend.services.Service import Service


ACTION_REQUEST_MAPPING = {
    ACTION_TYPE_IMAGE_BUILD: ImageBuildAction,
    ACTION_TYPE_WEBHOOK_NOTIFICATION: WebhookAction,
    ACTION_TYPE_CONTAINER_RUN: ContainerRunAction,
    ACTION_TYPE_TAPIS_JOB: TapisJobAction,
}

ACTION_REQUEST_TYPES = list(ACTION_REQUEST_MAPPING.keys())

class ActionService(Service):
    def __init__(self):
        Service.__init__(self)
        self._register_service("cred_service", CredentialsService)

    def create(self, pipeline, request):
        # Create the context
        context = None
        if request.context is not None:
            try:
                context = self._create_context(request, pipeline)
            except Exception as e:
                # TODO log the error
                self.rollback()
                raise e

        destination = None
        if request.destination is not None:
            try:
                destination = self._create_destination(request, pipeline)
            except Exception as e:
                # TODO log the error
                self.rollback()
                raise e
            
        # Create action
        try:
            action = Action.objects.create(
                auth=request.auth,
                auto_build=request.auto_build,
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
                id=request.id,
                output=request.output,
                pipeline=pipeline,
                poll=request.poll,
                query_params=request.query_params,
                type=request.type,
                depends_on=[ dict(item) for item in request.depends_on ],
                retries=request.retries,
                tapis_job_def=request.tapis_job_def,
                tapis_actor_id=request.tapis_actor_id,
                ttl=request.ttl,
                url=request.url,
            )
        except (IntegrityError, OperationalError, DatabaseError) as e:
            self.rollback()
            raise e

        return action

    def _resolve_authn_source(self, request, pipeline, accessor):
        """Determines whether the authn source will come and identity
        or credentials directly"""

        # Accessor is either "context" or "destination", and "target" is
        # the context or destination object of the action
        target = getattr(request, accessor)

        # Return the identity if one is provided
        identity_uuid = getattr(target, "identity_uuid", None)
        identity = None
        if identity_uuid != None:
            identity = Identity.objects.filter(pk=identity_uuid).first()

            return (identity, None)
        
        # Create the credentials for the context or destination if one is specified 
        # and no identity was provided
        credentials = getattr(target, "credentials", None)
        cred = None
        if credentials != None:
            cred_data = {}
            for key, value in dict(credentials).items():
                if value is not None:
                    cred_data[key] = getattr(credentials, key)
            
            try:
                cred_service = self._get_service("cred_service")
                cred = cred_service.save(f"pipeline:{pipeline.id}", cred_data)
                
                # Register a rollback funtion(partial) that will be used to delete the credentials
                # should any subsequent model creations fail
                self._add_rollback(cred_service.delete, cred.sk_id)
            except Exception as e:
                raise e
        
        return (None, cred)

    def _create_context(self, request, pipeline):
        (identity, cred) = self._resolve_authn_source(request, pipeline, "context")
        
        if (
            request.context.visibility == "private"
            and (identity == None and cred == None)
        ):
            raise Exception("Missing identity or credentials for private context")

        try:
            context = Context.objects.create(
                branch=request.context.branch,
                credentials=cred,
                dockerfile_path=request.context.dockerfile_path,
                sub_path=request.context.sub_path,
                type=request.context.type,
                url=request.context.url,
                visibility=request.context.visibility,
                identity=identity
            )

            # Register a rollback funtion(partial) that will be used to delete the context
            # should any subsequent model creations fail
            self._add_rollback(context.delete)
        except (IntegrityError, OperationalError) as e:
            raise e

        return context

    def _create_destination(self, request, pipeline):
        (identity, cred) = self._resolve_authn_source(request, pipeline, "destination")

         # Create the destination
        try:
            destination = Destination.objects.create(
                credentials=cred,
                tag=request.destination.tag,
                type=request.destination.type,
                url=request.destination.url,
                identity=identity
            )

            self._add_rollback(destination.delete)
        except (IntegrityError, OperationalError) as e:
            raise e

        return destination

    def resolve_request_type(self, action_type):
        return ACTION_REQUEST_MAPPING[action_type]

    def is_valid_action_type(self, action_type):
        if action_type in ACTION_REQUEST_MAPPING:
            return True

        return False

    def get_action_request_types(self):
        return ACTION_REQUEST_TYPES

service = ActionService()
