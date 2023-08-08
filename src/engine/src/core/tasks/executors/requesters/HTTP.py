import requests

from owe_python_sdk.TaskResult import TaskResult
from core.tasks.TaskExecutor import TaskExecutor


PERMITTED_HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]

# TODO Request Task needs to be containerized
class HTTP(TaskExecutor):
    def __init__(self, task, ctx, exchange, plugins=[]):
        TaskExecutor.__init__(self, task, ctx, exchange, plugins=plugins)

    def execute(self):
        if self.task.http_method.upper() not in PERMITTED_HTTP_METHODS:
            self.ctx.logger.info(
                f"Request Error: Method Not Allowed ({self.task.http_method})"
            )
            return TaskResult(
                status=405, errors=[f"Method Not Allowed ({self.task.method})"],
                stderr=self._tail_stderr(),
                stdout=self._tail_stdout()
            )

        try:
            # Calls the get, post, patch, etc. methods on the request object and sends the request
            # to the specified url
            response = getattr(requests, self.task.http_method)(
                self.task.url,
                data=self.task.data,
                headers=self.task.headers,
                params=self.task.query_params,
            )

            self._stdout(response.content)

            return TaskResult(
                status=0
                if response.status_code in range(200, 300)
                else response.status_code,
                stderr=self._tail_stderr(),
                stdout=self._tail_stdout()
            )

        except Exception as e:
            return TaskResult(1, errors=[str(e)], stderr=self._tail_stderr(), stdout=self._tail_stdout())
