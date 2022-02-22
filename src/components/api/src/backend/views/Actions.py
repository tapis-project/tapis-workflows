from backend.models import Action, ACTION_TYPES, ACTION_TYPE_WEBHOOK_NOTIFICATION, ACTION_TYPE_CONTAINER_BUILD, ACTION_TYPE_CONTAINER_EXEC
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.requests import WebhookActionCreateRequest, ContainerBuildActionCreateRequest, ContainerExecActionCreateRequest
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.errors import BadRequest
from backend.views.http.responses.models import ModelListResponse


ACTION_REQUEST_MAPPING = {
    ACTION_TYPE_CONTAINER_BUILD: ContainerBuildActionCreateRequest,
    ACTION_TYPE_WEBHOOK_NOTIFICATION: WebhookActionCreateRequest,
    ACTION_TYPE_CONTAINER_EXEC: ContainerExecActionCreateRequest
}

class Actions(RestrictedAPIView):
    def get(self, request):
        actions = Action.objects.all()

        return ModelListResponse(actions)

    def post(self, request):
        # Validate the request body
        if "type" not in self.request_body:
            return BadRequest(message="Request body missing 'type' property")

        if self.request_body["type"] not in ACTION_REQUEST_MAPPING:
            return BadRequest(message=f"Invalid action type: ({self.request_body['type']}). {ACTION_REQUEST_MAPPING.keys()}")

        # Resolve the the proper request for the type of action provided in the request body
        ActionCreateRequestType = ACTION_REQUEST_MAPPING[self.request_body["type"]]

        # Validate and prepare the create reqeust
        prepared_request = self.prepare(ActionCreateRequestType)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = prepared_request.body

        return BaseResponse()