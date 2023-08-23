import time

from contrib.tapis.helpers import TapisServiceAPIGateway
from contrib.tapis.constants import TAPIS_ACTOR_POLLING_FREQUENCY
from owe_python_sdk.TaskExecutor import TaskExecutor


class TapisActor(TaskExecutor):
    def __init__(self, task, ctx, exchange):
        TaskExecutor.__init__(self, task, ctx, exchange)
        self.executions = []

    def execute(self):
        try:
            tapis_service_api_gateway = TapisServiceAPIGateway()
            self.service_client = tapis_service_api_gateway.get_client()
            
            # Submit the message to abaco
            res = self.service_client.actors.send_message(
                actor_id=self.task.tapis_actor_id,
                # message=self.task.tapis_actor_message or "", # Send empty message
                message="This is a word count test",
                _tapis_set_x_headers_from_service=True,
                _x_tapis_tenant=self.ctx.params.tapis_tenant_id,
                _x_tapis_user=self.ctx.params.tapis_pipeline_owner
            )
            
            # End the task successfully with empty output
            if not self.task.poll:
                return self._task_result(0)

            # Fetch the execution
            execution = self._get_execution(self.task.tapis_actor_id, res.execution_id)
            
            # Polls the execution until it reaches a terminal state, then polls
            # the execution of linked actors recursively.
            # NOTE Actors can have only a single child
            self._poll_executions_recursively(execution)

            # Check for any failed executions and return failed task accordingly
            for execution in self.executions:
                if execution.status == "ERROR":
                    return self._task_result(1, errors=[f"Actor exited with status 'ERROR'. actor_id: {execution.actor_id} | execution_id: {execution.id}"])

            return self._task_result(0)
        except Exception as e:
            self.ctx.logger.error(f"ERROR IN TAPIS ACTOR: {str(e)}")
            return self._task_result(1, errors=[str(e)])

    def _poll_executions_recursively(self, execution):
        # Poll until the execution reaches a terminal state
        execution_status = execution.status
        while execution_status not in ["COMPLETED", "ERROR"]:
            # Sleep for the polling frequency time
            time.sleep(TAPIS_ACTOR_POLLING_FREQUENCY)       

            # Fetch the execution status
            execution = self._get_execution(execution.actor_id, execution.id)
            execution_status = execution.status

        # Add the execution to the executions list
        self.executions.append(execution)

        # If there is an error with the execution return from the loop
        if execution.status == "ERROR":
            return 
        
        # Get the logs of the execution and store them
        logs = self.service_client.actors.get_execution_logs(
            actor_id=execution.actor_id,
            execution_id=execution.id,
            _x_tapis_tenant=self.ctx.params.tapis_tenant_id,
            _x_tapis_user=self.ctx.params.tapis_pipeline_owner
        ).logs

        self._set_output(f"actors/{execution.actor_id}/.stdout", logs)

        execution_result = self.service_client.actors.get_execution_result(
            actor_id=execution.actor_id,
            execution_id=execution.id,
            _x_tapis_tenant=self.ctx.params.tapis_tenant_id,
            _x_tapis_user=self.ctx.params.tapis_pipeline_owner
        )

        self._set_output(f"actors/{execution.actor_id}/.result", execution_result)

        # Get linked actors' executions recursively
        if getattr(execution, "link", False) and getattr(execution, "next_execution_id", False):
            execution = self._get_execution(execution.link, execution.next_execution_id)
            self._poll_executions_recursively(execution)

    def _get_execution(self, actor_id, execution_id):
        return self.service_client.actors.get_execution(
            actor_id=actor_id,
            execution_id=execution_id,
            _x_tapis_tenant=self.ctx.params.tapis_tenant_id,
            _x_tapis_user=self.ctx.params.tapis_pipeline_owner
        )

    def _set_output(self, filename, value, flag="wb"):
        with open(f"{self.task.output_dir}{filename.lstrip('/')}", flag) as file:
            file.write(value)