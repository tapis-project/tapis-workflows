from django.db import IntegrityError
from backend.models import Action, Pipeline, Group, GroupUser
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.errors import BadRequest, UnprocessableEntity, Forbidden
from backend.views.http.responses.models import ModelListResponse, ModelResponse
from backend.services.ActionService import service


class Actions(RestrictedAPIView):
    def get(self, request):
        actions = Action.objects.all()

        return ModelListResponse(actions)

    def post(self, request):
        # Validate the request body
        if "type" not in self.request_body:
            return BadRequest(message="Request body missing 'type' property")

        if not service.is_valid_action_type(self.request_body["type"]):
            return BadRequest(message=f"Invalid action type: Expected one of: {service.get_action_request_types()} - Recieved: {self.request_body['type']}. ")

        # Resolve the the proper request for the type of action provided in the request body
        ActionRequest = service.resolve_request_type(self.request_body["type"])

        # Validate and prepare the create reqeust
        prepared_request = self.prepare(ActionRequest)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = prepared_request.body

        # Get the pipline for the new action
        pipeline = Pipeline.objects.filter(id=body.pipeline_id).first()

        # Return if BadRequest if no pipeline found
        if pipeline is None:
            return BadRequest(f"Pipline '{pipeline.id}' does not exist")

        # Ensure the user belongs to the group that owns the pipeline
        # Get the group
        group = Group.objects.filter(id=pipeline.group_id).first()

        # Check that the group_id passed by the user is a valid group
        if group is None:
            return UnprocessableEntity(f"Group '{pipeline.group_id}' does not exist'")

        # Get all the groups the user belongs to
        group_users = GroupUser.objects.filter(username=request.username)
        group_ids = [ group_user.group_id for group_user in group_users ]

        # Check that the user belongs to the group that is attached
        # to this pipline
        if pipeline.group_id not in group_ids:
            return Forbidden(message="You cannot create a an action for this pipeline")

        # Create action
        try:
            action = service.create(pipeline, body)
        except IntegrityError as e:
            return BadRequest(message=e.__cause__)

        return ModelResponse(action)