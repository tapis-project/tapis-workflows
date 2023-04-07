import json, re

from typing import AnyStr, List

from pydantic import ValidationError
from django.db import DatabaseError, IntegrityError, OperationalError
from django.core.exceptions import ValidationError as ModelValidationError

from backend.models import Task, Context, Destination, Identity
from backend.models import (
    TASK_TYPE_REQUEST,
    TASK_TYPE_IMAGE_BUILD,
    TASK_TYPE_CONTAINER_RUN,
    TASK_TYPE_TAPIS_JOB,
    TASK_TYPE_TAPIS_ACTOR,
    TASK_TYPE_FUNCTION,
    DESTINATION_TYPE_LOCAL,
    DESTINATION_TYPE_DOCKERHUB,
)
from backend.views.http.requests import (
    RequestTask,
    ImageBuildTask,
    ContainerRunTask,
    TapisJobTask,
    TapisActorTask,
    FunctionTask,
    RegistryDestination,
    LocalDestination,
    task_input_value_types,
    task_input_value_from_keys
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
    TASK_TYPE_FUNCTION: FunctionTask
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

            # Validate input TODO move validation logic to pydantic if possible
            err = self._validate_input(request.input)
            if err != None:
                raise Exception(f"Failed to validate input: {err}")

        except Exception as e:
            self.rollback()
            raise e


        # Create task
        try:
            task = Task.objects.create(
                auth=request.auth,
                builder=request.builder,
                cache=request.cache,
                code=request.code,
                command=request.command,
                context=context,
                data=request.data,
                description=request.description,
                destination=destination,
                headers=request.headers,
                http_method=request.http_method,
                image=request.image,
                input=request.input,
                installer=request.installer,
                id=request.id,
                output=request.output,
                packages=request.packages,
                pipeline=pipeline,
                poll=request.poll,
                query_params=request.query_params,
                runtime=request.runtime,
                type=request.type,
                depends_on=[ dict(item) for item in request.depends_on ],
                tapis_job_def=request.tapis_job_def,
                tapis_actor_id=request.tapis_actor_id,
                tapis_actor_message=self._tapis_actor_message_to_str(
                    request.tapis_actor_message
                ),
                url=request.url,
                # Exection profile
                flavor=request.execution_profile.flavor,
                max_exec_time=request.execution_profile.max_exec_time,
                max_retries=request.execution_profile.max_retries,
                invocation_mode=request.execution_profile.invocation_mode,
                retry_policy=request.execution_profile.retry_policy
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

        except Exception as e:
            print("Generic Exception", request.id, flush=True)
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
                    cred_data[key] = credentials.get(key)
            
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
        if type(message) == str:
            return message

        # Message is a dictionary. Convert to string and return
        return json.dumps(message)

    def _validate_input(self, _input):
        input_key_pattern = r"^[_]?[a-zA-Z]+[a-zA-Z0-9_]*"
        for key in _input:
            # Validate input key
            if not re.match(input_key_pattern, key):
                return "Disallowed input key: must conform to the following pattern: ^[_]*[a-zA-Z]+[a-zA-Z0-9]*"

            # Validate input value
            if type(_input[key]) != dict:
                return f"Input value must be a dict: type {type(_input[key])} found for key {key}"

            # Validate input value type property
            if _input[key].get("type", None) not in task_input_value_types:
                return f"'type' property input value of key {key} must be oneOf: {task_input_value_types}"

            # Return if the value property exists and is not None
            if _input[key].get("value", None) != None:
                return
            
            # Validate the value_from property of the input value
            value_from = _input[key].get("value_from", None)
            if type(value_from) != dict:
                return f"Input validation error at key {key}: 'value_from' must be a dictionary"

            # Validate the key of the value_from property
            value_from_key = list(value_from.keys())[0]
            if len(value_from) > 1 or value_from_key not in task_input_value_from_keys:
                return f"Input validation error at key {key}: The key in 'value_from' must be oneOf: {task_input_value_from_keys}" 
            
            # Validate value_from value for 'env' and 'params'
            value_from_value = value_from[value_from_key]
            if value_from_key != "task_output" and type(value_from_value) not in [str, int, float, AnyStr]:
                return f"Input validation error at key {key}: 'value_from' value type for keys [env|params] must be oneOf types [string, number, binary]"

            # Validate value_from value for "task_output"
            if (
                value_from_key == "task_output"
                and (
                    type(value_from_value) != dict
                    or value_from_value.get("task_id", None) == None
                    or value_from_value.get("output_id", None) == None
                )
                
            ):
                return f"Input validation error at key {key}: When referencing task outputs, 'value_from' value must be a dictionary with the following properties ['task_id', 'output_id']"

    def delete(self, tasks: List[Task]):
        for task in tasks:
            try:
                task.delete()
            except (DatabaseError, OperationalError) as e:
                raise ServerError(message=e.__cause__)
            except Exception as e:
                raise ServerError(message=str(e))

service = TaskService()
