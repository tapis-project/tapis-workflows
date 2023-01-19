import time

from helpers.TapisServiceAPIGateway import TapisServiceAPIGateway

from core.tasks.TaskResult import TaskResult
from core.tasks.TaskExecutor import TaskExecutor
from conf.constants import TAPIS_ACTOR_POLLING_FREQUENCY


class TapisActor(TaskExecutor):
    def __init__(self, task, ctx, exchange):
        TaskExecutor.__init__(self, task, ctx, exchange)
        self.executions = []

    def execute(self):
        try:
            tapis_service_api_gateway = TapisServiceAPIGateway()
            self.service_client = tapis_service_api_gateway.get_client()

            # Submit the job
            res = self.service_client.actors.send_message(
                actor_id=self.task.actor_id,
                message=self.task.message,
                _x_tapis_tenant=self.ctx.group.tenant_id,
                _x_tapis_user=self.ctx.pipeline.owner
            )
            
            # End the task successfully with empty output
            if not self.task.poll:
                return TaskResult(0)

            # Fetch the execution
            execution = self._get_execution(self.task.actor_id, res.execution_id)
            
            # Polls the execution until it reaches a terminal state, then polls
            # the execution of linked actors recursively.
            # NOTE Actors can have only a single child
            self._poll_executions_recursively(execution)

            # Check for any failed executions and return failed task accordingly
            for execution in self.executions:
                if execution.status == "ERROR":
                    return TaskResult(1, errors=[f"Actor exited with status 'ERROR'. actor_id: {execution.actor_id} | execution_id: {execution.id}"])

            # TODO set outputs on the task result
            return TaskResult(0)
        except Exception as e:
            return TaskResult(1, errors=[str(e)])

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
            _x_tapis_tenant=self.ctx.group.tenant_id,
            _x_tapis_user=self.ctx.pipeline.owner
        ).logs

        self._store_result(f"actors/{execution.actor_id}/.stdout", logs)

        execution_result = self.service_client.actors.get_execution_result(
            actor_id=execution.actor_id,
            execution_id=execution.id,
            _x_tapis_tenant=self.ctx.group.tenant_id,
            _x_tapis_user=self.ctx.pipeline.owner
        )

        self._store_result(f"actors/{execution.actor_id}/.result", execution_result)

        # Get linked actors' executions recursively
        if getattr(execution, "link", False) and getattr(execution, "next_execution_id", False):
            execution = self._get_execution(execution.link, execution.next_execution_id)
            self._poll_executions_recursively(execution)

    def _get_execution(self, actor_id, execution_id):
        return self.service_client.actors.get_execution(
            actor_id=actor_id,
            execution_id=execution_id,
            _x_tapis_tenant=self.ctx.group.tenant_id,
            _x_tapis_user=self.ctx.pipeline.owner
        )

    def _store_result(self, filename, value, flag="wb"):
        with open(f"{self.task.output_dir}{filename.lstrip('/')}", flag) as file:
            file.write(value)