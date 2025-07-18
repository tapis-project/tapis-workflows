import json

from typing import List

from pydantic import ValidationError, BaseModel
from django.db import DatabaseError, IntegrityError, OperationalError
from django.core.exceptions import ValidationError as ModelValidationError

from backend.models import Task, TaskTag, Context, Destination, Identity 
from backend.models import (
    TASK_TYPE_REQUEST,
    TASK_TYPE_IMAGE_BUILD,
    TASK_TYPE_APPLICATION,
    TASK_TYPE_CONTAINER_RUN,  # Keep for backwards compatibility. container_run renamed to application
    TASK_TYPE_TAPIS_JOB,
    TASK_TYPE_TAPIS_ACTOR,
    TASK_TYPE_FUNCTION,
    TASK_TYPE_TEMPLATE,
    DESTINATION_TYPE_LOCAL,
    DESTINATION_TYPE_DOCKERHUB,
)
from backend.views.http.requests import (
    RequestTask,
    ImageBuildTask,
    ApplicationTask,
    TapisJobTask,
    TapisActorTask,
    FunctionTask,
    TemplateTask,
    DockerhubDestination,
    LocalDestination
)
from backend.services.CredentialsService import service as credentials_service
from backend.services.TaskTagService import service as task_tag_service;
from backend.services.Service import Service
from backend.errors.api import BadRequestError, ServerError


TASK_TYPE_REQUEST_MAPPING = {
    TASK_TYPE_IMAGE_BUILD: ImageBuildTask,
    TASK_TYPE_REQUEST: RequestTask,
    TASK_TYPE_APPLICATION: ApplicationTask,
    TASK_TYPE_CONTAINER_RUN: ApplicationTask, # Keep for backwards compatibility. container_run renamed to application
    TASK_TYPE_TAPIS_JOB: TapisJobTask,
    TASK_TYPE_TAPIS_ACTOR: TapisActorTask,
    TASK_TYPE_FUNCTION: FunctionTask,
    TASK_TYPE_TEMPLATE: TemplateTask
}

DESTINATION_TYPE_REQUEST_MAPPING = {
    DESTINATION_TYPE_DOCKERHUB: DockerhubDestination,
    DESTINATION_TYPE_LOCAL: LocalDestination
}

TASK_REQUEST_TYPES = list(TASK_TYPE_REQUEST_MAPPING.keys())

class TaskService(Service):
    def __init__(self):
        Service.__init__(self)

    def create(self, pipeline, newTask):
        context = None
        destination = None
        try:
            if newTask.type == "image_build":
                # Create the context
                if newTask.context != None:
                    context = self._create_context(newTask, pipeline)
                # Create the destination
                if newTask.destination != None:
                    destination = self._create_destination(newTask, pipeline)

        except Exception as e:
            self.rollback()
            raise e

        # Convert the input and output to jsonserializable
        _input = {}
        for key in newTask.input:
            _input[key] = newTask.input[key].dict()

        output = {}
        for key in newTask.output:
            output[key] = newTask.output[key].dict()

        # Prepare the uses property
        uses = getattr(newTask, "uses", None)
        if uses != None:
            uses = uses.dict()

        # Create task
        try:
            task = Task.objects.create(
                auth=getattr(newTask, "auth", None),
                builder=getattr(newTask, "builder", None),
                cache=getattr(newTask, "cache", None),
                code=getattr(newTask, "code", None),
                command=getattr(newTask, "command", None),
                context=context,
                conditions=[
                    self._recursive_pydantic_model_to_dict(c) 
                    for c in getattr(newTask, "conditions", [])
                ],
                data=getattr(newTask, "data", None),
                description=newTask.description,
                destination=destination,
                headers=getattr(newTask, "headers", None),
                http_method=getattr(newTask, "http_method", None),
                # Set to None if the newTask contains no git repositories, else, set as an array of dicts of git repos
                git_repositories=(
                    [ dict(item) for item in getattr(newTask, "git_repositories", []) ]
                    if getattr(newTask, "git_repositories") != None
                    else None
                ),
                image=getattr(newTask, "image", None),
                input=_input,
                installer=getattr(newTask, "installer", None),
                id=newTask.id,
                output=output,
                packages=getattr(newTask, "packages", None),
                pipeline=pipeline,
                poll=getattr(newTask, "poll", None),
                query_params=getattr(newTask, "query_params", None),
                runtime=getattr(newTask, "runtime", None),
                type=newTask.type,
                depends_on=[ dict(item) for item in newTask.depends_on ],
                tapis_job_def=getattr(newTask, "tapis_job_def", None),
                tapis_actor_id=getattr(newTask, "tapis_actor_id", None),
                tapis_actor_message=self._tapis_actor_message_to_str(
                    getattr(newTask, "tapis_actor_message", None)
                ),
                url=getattr(newTask, "url", None),
                uses=uses,
                # Exection profile
                flavor=newTask.execution_profile.flavor,
                max_exec_time=newTask.execution_profile.max_exec_time,
                max_retries=newTask.execution_profile.max_retries,
                invocation_mode=newTask.execution_profile.invocation_mode,
                retry_policy=newTask.execution_profile.retry_policy
            )

            # TODO Calls the validators on the task model
            # task.clean()
        except (IntegrityError, OperationalError, DatabaseError) as e:
            self.rollback()
            raise e
        except BadRequestError as e:
            self.rollback()
            raise e
        except ModelValidationError as e:
            self.rollback()
            raise e
        except ServerError as e:
            self.rollback()
            raise e
        except Exception as e:
            print(f"Unexpected Error: {e}", flush=True)
            self.rollback()
            raise e
        
        try:
            task_tag_service.batch_create(task, getattr(newTask, "tags", []))
        except (IntegrityError, OperationalError, DatabaseError) as e:
            print(f"Failed creating tags for task '{task.id}': {e}", flush=True)
            self.rollback()
            raise e
        except Exception as e:
            print(f"Unexpected Error when creating tags for task '{task.id}': {e}", flush=True)
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
                cred = credentials_service.save(f"pipeline:{pipeline.id}", cred_data)
                
                # Register a rollback funtion(partial) that will be used to delete the credentials
                # should any subsequent model creations fail
                self._add_rollback(credentials_service.delete, cred.sk_id)
            except Exception as e:
                raise ServerError(str(e))
        
        return (None, cred)

    def _create_context(self, request, pipeline):
        """Creates the Context object for the task. The Context contains
        data about the source of the build; which registry to pull from, the
        path to the build file, etc"""

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
                recipe_file_path=request.context.build_file_path,
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

    def _tapis_actor_message_to_str(self, message):
        # Simply pass the message back if already a string
        if type(message) in [str, None]:
            return message

        # Message is a dictionary. Convert to string and return
        return json.dumps(message)

    def delete(self, tasks: List[Task]):
        for task in tasks:
            try:
                task.delete()
            except (DatabaseError, OperationalError) as e:
                raise ServerError(message=e.__cause__)
            except Exception as e:
                raise ServerError(message=str(e))
            
    def _recursive_pydantic_model_to_dict(self, obj):
        if type(obj) in [list, tuple]:
            items = type(obj)()
            for item in obj:
                items.append(self._recursive_pydantic_model_to_dict(item))
            return items
        if type(obj) == dict:
            modified_dict = {}
            for key in obj:
                modified_dict[key] = self._recursive_pydantic_model_to_dict(obj[key])
            return modified_dict
        if isinstance(obj, BaseModel):
            dict_obj = obj.dict()
            modified_dict = {}
            for key in dict_obj:
                modified_dict[key] = self._recursive_pydantic_model_to_dict(dict_obj[key])
            return modified_dict

        return obj

service = TaskService()
