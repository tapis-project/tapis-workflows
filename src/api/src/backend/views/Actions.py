import json

from django.db import IntegrityError, OperationalError
from backend.models import Action, Pipeline, Group
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses import BaseResponse, ResourceURLResponse
from backend.views.http.responses.errors import BadRequest, UnprocessableEntity, Forbidden, NotFound, MethodNotAllowed, ServerError
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.services.ActionService import service as action_service
from backend.services.GroupService import service as group_service
from backend.helpers import resource_url_builder


class Actions(RestrictedAPIView):

    def get(self, request, group_id, pipeline_id, action_id=None):
        if action_id is None:
            return self.list(request, pipeline_id)

        # Get the pipline
        pipeline = Pipeline.objects.filter(
            group_id=group_id,
            id=pipeline_id
        ).first()

        # Return if BadRequest if no pipeline found
        if pipeline is None:
            return BadRequest(f"Pipline '{pipeline_id}' does not exist")

        # Check that the user belongs to the group that is attached
        # to this pipline
        if not group_service.user_in_group(request.username, group_id):
            return Forbidden(message="You cannot view actions for this pipeline")

        action = Action.objects.filter(pipeline=pipeline_id, id=action_id).first()

        if action is None:
            return NotFound(f"Action with id '{action_id}' not found in pipeline '{pipeline_id}'")

        return ModelResponse(action)


    def list(self, request, group_id, pipeline_id, *args, **kwargs):
        # Get the pipline
        pipeline = Pipeline.objects.filter(
            group_id=group_id,
            id=pipeline_id
        ).first()

        # Return if BadRequest if no pipeline found
        if pipeline is None:
            return BadRequest(f"Pipline '{pipeline_id}' does not exist")

        # Get the group
        group = Group.objects.filter(id=group_id).first()

        # Check that the group_id passed by the user is a valid group
        if group is None:
            return UnprocessableEntity(f"Group '{group_id}' does not exist'")

        # Check that the user belongs to the group that is attached
        # to this pipline
        if not group_service.user_in_group(request.username, group_id):
            return Forbidden(message="You cannot view actions for this pipeline")
            
        actions = Action.objects.filter(pipeline=pipeline_id)

        return ModelListResponse(actions)
    
    def post(self, request, group_id, pipeline_id, *args, **kwargs):
        # Validate the request body
        if "type" not in self.request_body:
            return BadRequest(message="Request body missing 'type' property")

        if not action_service.is_valid_action_type(self.request_body["type"]):
            return BadRequest(message=f"Invalid action type: Expected one of: {action_service.get_action_request_types()} - Recieved: {self.request_body['type']}. ")

        # Ensure the user belongs to the group that owns the pipeline
        # Get the group
        group = Group.objects.filter(id=group_id).first()

        # Check that the group_id passed by the user is a valid group
        if group is None:
            return UnprocessableEntity(f"Group '{group_id}' does not exist'")

        # Check that the user belongs to the group that is attached
        # to this pipline
        if not group_service.user_in_group(request.username, group_id):
            return Forbidden(message="You cannot create a an action for this pipeline")

        # Resolve the the proper request for the type of action provided in the request body
        ActionRequest = action_service.resolve_request_type(self.request_body["type"])

        # Validate and prepare the create reqeust
        prepared_request = self.prepare(ActionRequest)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = prepared_request.body

        # Get the pipline for the new action
        pipeline = Pipeline.objects.filter(
            group_id=group_id,
            id=pipeline_id
        ).first()

        # Return if BadRequest if no pipeline found
        if pipeline is None:
            return BadRequest(f"Pipline '{pipeline_id}' does not exist")

        # Create action
        try:
            action = action_service.create(pipeline, body)
        except (IntegrityError, OperationalError) as e:
            return BadRequest(message=e.__cause__)

        return ResourceURLResponse(
            url=resource_url_builder(request.url, action.id))


    def put(self, request, group_id, pipeline_id, action_id=None):
        # Get the pipline
        pipeline = Pipeline.objects.filter(
            group_id=group_id,
            id=pipeline_id
        ).first()

        # Return if BadRequest if no pipeline found
        if pipeline is None:
            return BadRequest(f"Pipline '{pipeline_id}' does not exist")

        # Check that the user belongs to the group that is attached
        # to this pipline
        if not group_service.user_in_group(request.username, group_id):
            return Forbidden(message="You cannot update actions for this pipeline")

        action = Action.objects.filter(pipeline=pipeline_id, id=action_id).first()

        if action is None:
            return NotFound(f"Action with id '{action_id}' not found in pipeline '{pipeline_id}'")

        # Validate the request body
        if "type" not in self.request_body:
            return BadRequest(message="Request body missing 'type' property")

        if not action_service.is_valid_action_type(self.request_body["type"]):
            return BadRequest(message=f"Invalid action type: Expected one of: {action_service.get_action_request_types()} - Recieved: {self.request_body['type']}. ")

        # Resolve the the proper request for the type of action provided in the request body
        ActionRequest = action_service.resolve_request_type(self.request_body["type"])

        # Validate and prepare the create reqeust
        prepared_request = self.prepare(ActionRequest)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = prepared_request.body

        # Disallow updating the type property
        if body.type != action.type:
            return BadRequest(f"Updating the type of an action is not allowed. Expected action.type: {action.type} - Recieved: {'null' if body.type is None else body.type}")

        # The pipeline_id property will be set to the previous value as we do not
        # allow that property to be updated
        Action.objects.filter(
            pipeline_id=pipeline_id,
            id=action_id
        ).update(**{
            **json.loads(body.json()),
            "type": action.type,
            "pipeline_id": pipeline_id,
            "context": action.context,
            "destination": action.destination
        })

        return ModelResponse(Action.objects.filter(id=body.id, pipeline_id=pipeline_id).first())

    def patch(self, *_, **__):
        return MethodNotAllowed("Method 'PATCH' not allowed for 'Action' objects")

    def delete(self, request, group_id, pipeline_id, action_id):
        # Get the pipline
        pipeline = Pipeline.objects.filter(
            group_id=group_id,
            id=pipeline_id
        ).first()

        # Check that the user belongs to the group that is attached
        # to this pipline
        if not group_service.user_in_group(request.username, group_id):
            return Forbidden(message="You cannot update actions for this pipeline")

        # Return if BadRequest if no pipeline found
        if pipeline is None:
            return BadRequest(f"Pipline '{pipeline_id}' does not exist")

        action = Action.objects.filter(pipeline=pipeline_id, id=action_id).first()

        if action is None:
            return NotFound(f"Action with id '{action_id}' not found in pipeline '{pipeline_id}'")

        try:
            action.delete()
        except Exception as e:
            return ServerError(str(e))

        return BaseResponse(message=f"Deleted action '{action_id}' on pipeline '{pipeline_id}")

        