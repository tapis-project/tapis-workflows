import requests, json

from typing import Any, Dict, Union

from pydantic import BaseModel, ValidationError

from core.ActionResult import ActionResult


PERMITTED_HTTP_METHODS = [ "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD" ]

class WebhookAction(BaseModel):
    auth: Union[dict, None] = None,
    data: Any = None,
    headers: Dict[str, Union[str, int,]] = None
    http_method: str
    query_params: Dict[str, Union[str, int,]] = None
    url: str

# TODO Webhook Notifcation Action needs to be containerized
class Webhook:
    def execute(self, action):
        try:
            webhook_action = WebhookAction(**vars(action))
        except ValidationError as e:
            errors = [ f"{error['type']}. {error['msg']}: {'.'.join(error['loc'])}" for error in json.loads(e.json())]
            print(f"Webhook Notification Error: {errors}")
            return ActionResult(status=400, errors=errors)

        if webhook_action.http_method.upper() not in PERMITTED_HTTP_METHODS:
            print(f"Webhook Notification Error: Method Not Allowed ({webhook_action.http_method})")
            return ActionResult(status=405, errors=[f"Method Not Allowed ({webhook_action.method})"])

        try:
            # Calls the get, post, patch, etc. methods on the request object and sends the request
            # to the specified url
            response = getattr(requests, webhook_action.http_method)(
                webhook_action.url,
                data=webhook_action.data,
                headers=webhook_action.headers,
                params=webhook_action.query_params,
            )

            return ActionResult(
                status=0 if response.status_code in range(200, 300) else response.status_code,
                data=response.json()
            )

        except Exception as e:
            return ActionResult(1, errors=[str(e)])

executor = Webhook()