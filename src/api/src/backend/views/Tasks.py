import json

from django.db import IntegrityError, OperationalError

from backend.models import Task, Pipeline
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses import BaseResponse, ResourceURLResponse
from backend.views.http.responses.errors import BadRequest, Forbidden, NotFound, MethodNotAllowed, ServerError
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.services.TaskService import service as task_service
from backend.services.GroupService import service as group_service
from backend.helpers import resource_url_builder


class Tasks(RestrictedAPIView):
    def get(self, request, group_id, pipeline_id, task_id=None):
        # Get the group
        group = group_service.get(group_id, request.tenant_id)
        if group == None:
            return NotFound(f"No group found with id '{group_id}'")

        # Check that the user belongs to the group
        if not group_service.user_in_group(request.username, group_id, request.tenant_id):
            return Forbidden(message="You do not have access to this group")

        # Get the pipline
        pipeline = Pipeline.objects.filter(
            group=group,
            id=pipeline_id
        ).first()

        # Return if BadRequest if no pipeline found
        if pipeline == None:
            return BadRequest(f"Pipline with id '{pipeline_id}' does not exist")
        
        if task_id == None:
            return self.list(pipeline)

        # Check that the user belongs to the group that is attached
        # to this pipline
        if not group_service.user_in_group(request.username, group_id, request.tenant_id):
            return Forbidden(message="You cannot view tasks for this pipeline")

        task = Task.objects.filter(pipeline=pipeline, id=task_id).first()

        if task == None:
            return NotFound(f"Task with id '{task_id}' does not exists for pipeline '{pipeline_id}'")

        return ModelResponse(task)


    def list(self, pipeline, *_, **__):    
        return ModelListResponse(Task.objects.filter(pipeline=pipeline))
    
    def post(self, request, group_id, pipeline_id, *_, **__):
        # Validate the request body
        if "type" not in self.request_body:
            return BadRequest(message="Request body missing 'type' property")

        if not task_service.is_valid_task_type(self.request_body["type"]):
            return BadRequest(message=f"Invalid task type: Expected one of: {task_service.get_task_request_types()} - Recieved: {self.request_body['type']}. ")
        
        # Resolve the the proper request for the type of task provided in the request body
        TaskRequest = task_service.resolve_request_type(self.request_body["type"])
        
        # Validate and prepare the create reqeust
        prepared_request = self.prepare(TaskRequest)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = prepared_request.body

        # Get the group
        group = group_service.get(group_id, request.tenant_id)
        if group == None:
            return NotFound(f"No group found with id '{group_id}'")

        # Check that the user belongs to the group
        if not group_service.user_in_group(request.username, group_id, request.tenant_id):
            return Forbidden(message="You do not have access to this group")

        # Get the pipline
        pipeline = Pipeline.objects.filter(
            group=group,
            id=pipeline_id
        ).first()

        # Return if BadRequest if no pipeline found
        if pipeline == None:
            return BadRequest(f"Pipline with id '{pipeline_id}' does not exist")

        # Create task
        try:
            task = task_service.create(pipeline, body)
        except (IntegrityError, OperationalError) as e:
            return BadRequest(message=e.__cause__)
        except Exception as e:
            return ServerError(f"{e}")

        return ResourceURLResponse(
            url=resource_url_builder(request.url, task.id))


    def put(self, request, group_id, pipeline_id, task_id=None):
        # Get the group
        group = group_service.get(group_id, request.tenant_id)
        if group == None:
            return NotFound(f"No group found with id '{group_id}'")

        # Check that the user belongs to the group
        if not group_service.user_in_group(request.username, group_id, request.tenant_id):
            return Forbidden(message="You do not have access to this group")

        # Get the pipline
        pipeline = Pipeline.objects.filter(
            group=group,
            id=pipeline_id
        ).first()

        task = Task.objects.filter(pipeline=pipeline, id=task_id).first()

        if task == None:
            return NotFound(f"Task with id '{task_id}' not found in pipeline '{pipeline_id}'")

        # Validate the request body
        if "type" not in self.request_body:
            return BadRequest(message="Request body missing 'type' property")

        if not task_service.is_valid_task_type(self.request_body["type"]):
            return BadRequest(message=f"Invalid task type: Expected one of: {task_service.get_task_request_types()} - Recieved: {self.request_body['type']}. ")

        # Resolve the the proper request for the type of task provided in the request body
        TaskRequest = task_service.resolve_request_type(self.request_body["type"])

        # Validate and prepare the create reqeust
        prepared_request = self.prepare(TaskRequest)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = prepared_request.body

        # Disallow updating the type property
        if body.type != task.type:
            return BadRequest(f"Updating the type of an task is not allowed. Expected task.type: {task.type} - Recieved: {'null' if body.type == None else body.type}")

        # The pipeline_id property will be set to the previous value as we do not
        # allow that property to be updated
        Task.objects.filter(
            pipeline_id=pipeline_id,
            id=task_id
        ).update(**{
            **json.loads(body.json()),
            "type": task.type,
            "pipeline_id": pipeline_id,
            "context": task.context,
            "destination": task.destination
        })

        return ModelResponse(Task.objects.filter(id=body.id, pipeline_id=pipeline_id).first())

    def patch(self, *_, **__):
        return MethodNotAllowed("Method 'PATCH' not allowed for 'Task' objects")

    def delete(self, request, group_id, pipeline_id, task_id):
        # Get the group
        group = group_service.get(group_id, request.tenant_id)
        if group == None:
            return NotFound(f"No group found with id '{group_id}'")

        # Check that the user belongs to the group
        if not group_service.user_in_group(request.username, group_id, request.tenant_id):
            return Forbidden(message="You do not have access to this group")

        # Get the pipline
        pipeline = Pipeline.objects.filter(
            group=group,
            id=pipeline_id
        ).first()

        task = Task.objects.filter(pipeline=pipeline, id=task_id).first()

        if task == None:
            return NotFound(f"Task with id '{task_id}' not found in pipeline '{pipeline_id}'")

        try:
            task.delete()
        except Exception as e:
            return ServerError(str(e))

        return BaseResponse(message=f"Deleted task '{task_id}' on pipeline '{pipeline_id}")

        