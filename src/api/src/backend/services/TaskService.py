import logging, json

from pydantic import ValidationError
from django.db import DatabaseError, IntegrityError, OperationalError

from backend.models import Task, Context, Destination, Identity
from backend.models import (
    TASK_TYPE_REQUEST,
    TASK_TYPE_IMAGE_BUILD,
    TASK_TYPE_CONTAINER_RUN,
    TASK_TYPE_TAPIS_JOB,
    TASK_TYPE_TAPIS_ACTOR,
    DESTINATION_TYPE_LOCAL,
    DESTINATION_TYPE_DOCKERHUB,
)
from backend.views.http.requests import (
    RequestTask,
    ImageBuildTask,
    ContainerRunTask,
    TapisJobTask,
    TapisActorTask,
    RegistryDestination,
    LocalDestination
)
from backend.services.SecretService import service as secret_service
from backend.services.Service import Service
from backend.errors.api import BadRequestError, ServerError


TASK_TYPE_REQUEST_MAPPING = {
    TASK_TYPE_IMAGE_BUILD: ImageBuildTask,
    TASK_TYPE_REQUEST: RequestTask,
    TASK_TYPE_CONTAINER_RUN: ContainerRunTask,
    TASK_TYPE_TAPIS_JOB: TapisJobTask,
    TASK_TYPE_TAPIS_ACTOR: TapisActorTask,
}

DESTINATION_TYPE_REQUEST_MAPPING = {
    DESTINATION_TYPE_DOCKERHUB: RegistryDestination,
    DESTINATION_TYPE_LOCAL: LocalDestination
}

TASK_REQUEST_TYPES = list(TASK_TYPE_REQUEST_MAPPING.keys())

class TaskService(Service):
    def __init__(self):
        Service.__init__(self)

    def create(self, pipeline, request):
        try:
            # Create the context
            context = None
            if request.context != None:
                context = self._create_context(request, pipeline)
            
            # Create the destination
            destination = None
            if request.destination != None:
                destination = self._create_destination(request, pipeline)

        except Exception as e:
            self.rollback()
            raise e

        # Create task
        try:
            task = Task.objects.create(
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
                max_exec_time=request.max_exec_time,
                url=request.url,
            )
        except (IntegrityError, OperationalError, DatabaseError) as e:
            self.rollback()
            raise e

        except BadRequestError as e:
            self.rollback()
            raise e

        return task

    def _resolve_authn_source(self, request, pipeline, accessor):
        """Determines whether the authn source will come and identity
        or credentials directly"""

        # Accessor is either "context" or "destination", and "target" is
        # the context or destination object of the task
        target = getattr(request, accessor)

        # Return the identity if one is provided
        identity_uuid = getattr(target, "identity_uuid", None)
        identity = None
        if identity_uuid != None:
            # Ensure has access to this identity.
            # TODO Implement identity policies that allow group users access to this identity
            identity = Identity.objects.filter(pk=identity_uuid, owner=pipeline.owner).first()
            if identity == None:
                raise BadRequestError(f"Identity with uuid '{identity_uuid}' does not exist or you do not have access to it.")

            return (identity, None)
        
        # Create the credentials for the context or destination if one is specified 
        # and no identity was provided
        credentials = getattr(target, "credentials", None)
        cred = None
        if credentials != None:
            cred_data = {}
            for key, value in dict(credentials).items():
                if value != None:
                    cred_data[key] = getattr(credentials, key)
            
            try:
                cred = secret_service.save(f"pipeline:{pipeline.id}", cred_data)
                
                # Register a rollback funtion(partial) that will be used to delete the credentials
                # should any subsequent model creations fail
                self._add_rollback(secret_service.delete, cred.sk_id)
            except Exception as e:
                raise ServerError(str(e))
        
        return (None, cred)

    def _create_context(self, request, pipeline):
        """Creates the Context object for the task. The Context contains
        data about the source of the build; which registry to pull from, the
        path to the recipe file, etc"""

        # Resolve the authentication source for the context
        try:
            (identity, cred) = self._resolve_authn_source(request, pipeline, "context")
        except (BadRequestError, ServerError)as e:
            raise e

        # Create the context object for the task.
        try:
            context = Context.objects.create(
                branch=request.context.branch,
                credentials=cred,
                recipe_file_path=request.context.recipe_file_path,
                sub_path=request.context.sub_path,
                type=request.context.type,
                url=request.context.url,
                visibility=request.context.visibility,
                identity=identity,
                tag=request.context.tag
            )

            # Register a rollback funtion(partial) that will be used to delete the context
            # should any subsequent model creations fail
            self._add_rollback(context.delete)
        except (IntegrityError, OperationalError) as e:
            raise e
        except Exception as e:
            raise e

        return context

    def _create_destination(self, request, pipeline):
        # Resolve the authentication source.
        (identity, cred) = self._resolve_authn_source(request, pipeline, "destination")

        # Validate the the destination portion of the request
        request_schema = DESTINATION_TYPE_REQUEST_MAPPING[request.destination.type]

        # Create the destination
        try:
            # Validate the destination part of the request
            request_object = request_schema(**dict(request.destination))

            # Persist the Destination object
            destination = Destination.objects.create(
                credentials=cred,
                tag=getattr(request_object, "tag", None),
                type=request_object.type,
                url=getattr(request_object, "url", None),
                filename=getattr(request_object, "filename", None),
                identity=identity
            )

            # Register a rollback funtion(partial) that will be used to delete the destination
            # should any subsequent model creations fail
            self._add_rollback(destination.delete)
        except (IntegrityError, OperationalError) as e:
            self.rollback()
            raise e
        except ValidationError as e:
            self.rollback()
            errors = [f"{error['type']}. {error['msg']}: {'.'.join(error['loc'])}" for error in json.loads(e.json())]
            raise BadRequestError(str(errors))
        except Exception as e:
            self.rollback()
            raise e

        return destination

    def resolve_request_type(self, task_type):
        return TASK_TYPE_REQUEST_MAPPING[task_type]

    def is_valid_task_type(self, task_type):
        if task_type in TASK_TYPE_REQUEST_MAPPING:
            return True

        return False

    def is_valid_destination_type(self, destination_type):
        if destination_type in DESTINATION_TYPE_REQUEST_MAPPING:
            return True

        return False

    def get_task_request_types(self):
        return TASK_REQUEST_TYPES

service = TaskService()
