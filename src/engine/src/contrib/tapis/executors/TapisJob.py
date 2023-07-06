import json, time

from contrib.tapis.helpers import TapisServiceAPIGateway
from contrib.tapis.constants import TAPIS_JOB_POLLING_FREQUENCY

from owe_python_sdk.TaskResult import TaskResult
from core.tasks.TaskExecutor import TaskExecutor


class TapisJob(TaskExecutor):
    def __init__(self, task, ctx, exchange, plugins=[]):
        TaskExecutor.__init__(self, task, ctx, exchange, plugins=plugins)

    def execute(self):
        try:
            tapis_service_api_gateway = TapisServiceAPIGateway()
            service_client = tapis_service_api_gateway.get_client()

            # Recursively convert nested simple namespace objects to dict
            job_def = json.loads(json.dumps(self.task.tapis_job_def, default=lambda s: s.__dict__))

            # Add timestamp on job name to ensure unique name on submit
            job_def["name"] += str(time.time())

            # Submit the job
            job = service_client.jobs.submitJob(
                **job_def,
                _x_tapis_tenant=self.ctx.params.tapis_tenant_id,
                _x_tapis_user=self.ctx.params.tapis_pipeline_owner
            )

            # Get the initial job status
            job_status = job.status

            if self.task.poll:
                # Keep polling until the job is complete
                while job_status not in ["FINISHED", "CANCELLED", "FAILED"]:
                    # Wait the polling frequency time then try poll again
                    time.sleep(TAPIS_JOB_POLLING_FREQUENCY)
                    job_status = service_client.jobs.getJobStatus(
                        jobUuid=job.uuid,
                        _x_tapis_tenant=self.ctx.params.tapis_tenant_id,
                        _x_tapis_user=self.ctx.params.tapis_pipeline_owner
                    ).status

                output = {"jobUuid": job.uuid, "status": job_status}

                # Return a task result based on the final status of the tapis job
                if job_status == "FINISHED":
                    return TaskResult(0, output=output)

                return TaskResult(1, output=output)
                
            return TaskResult(0, output={"jobUuid": job.uuid, "status": job_status})

        except Exception as e:
            self.ctx.logger.error(f"ERROR IN TAPIS JOB: {str(e)}")
            return TaskResult(1, errors=[str(e)])