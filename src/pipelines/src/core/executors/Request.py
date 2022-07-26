import requests, json, logging

from typing import Any, Dict, Union

from pydantic import BaseModel, ValidationError

from core.TaskResult import TaskResult
from core.TaskExecutor import TaskExecutor


PERMITTED_HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]

class RequestModel(BaseModel):
    auth: Union[dict, None] = (None,)
    data: Any = (None,)
    headers: Dict[
        str,
        Union[
            str,
            int,
        ],
    ] = None
    http_method: str
    query_params: Dict[
        str,
        Union[
            str,
            int,
        ],
    ] = None
    url: str


# TODO Request Task needs to be containerized
class Request(TaskExecutor):
    def __init__(self, task, message):
        TaskExecutor.__init__(self, task, message)

    def execute(self, on_finish_callback):
        try:
            request_task = RequestModel(
                auth=self.task.auth,
                data=self.task.data,
                headers=self.task.headers,
                http_method=self.task.http_method,
                query_params=self.task.query_params,
                url=self.task.url,
            )
        except ValidationError as e:
            errors = [
                f"{error['type']}. {error['msg']}: {'.'.join(error['loc'])}"
                for error in json.loads(e.json())
            ]
            logging.info(f"Request Error: {errors}")
            return TaskResult(status=400, errors=errors)

        if request_task.http_method.upper() not in PERMITTED_HTTP_METHODS:
            logging.info(
                f"Request Error: Method Not Allowed ({request_task.http_method})"
            )
            return TaskResult(
                status=405, errors=[f"Method Not Allowed ({request_task.method})"]
            )

        try:
            # Calls the get, post, patch, etc. methods on the request object and sends the request
            # to the specified url
            response = getattr(requests, request_task.http_method)(
                request_task.url,
                data=request_task.data,
                headers=request_task.headers,
                params=request_task.query_params,
            )

            self._store_result(".stdout", response.content)

            return TaskResult(
                status=0
                if response.status_code in range(200, 300)
                else response.status_code
            )

        except Exception as e:
            return TaskResult(1, errors=[str(e)])
