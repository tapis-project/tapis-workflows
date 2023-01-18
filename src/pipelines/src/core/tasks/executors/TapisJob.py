import json

from time import time

from helpers.TapisServiceAPIGateway import TapisServiceAPIGateway

from core.tasks.TaskResult import TaskResult
from core.tasks.TaskExecutor import TaskExecutor
from conf.constants import TAPIS_JOB_POLLING_FREQUENCY


class TapisJob(TaskExecutor):
    def __init__(self, task, ctx, exchange):
        TaskExecutor.__init__(self, task, ctx, exchange)

    def execute(self):
        try:
            tapis_service_api_gateway = TapisServiceAPIGateway()
            service_client = tapis_service_api_gateway.get_client()

            # Recursively convert nested simple namespace objects to dict
            job_def = json.loads(json.dumps(self.task.tapis_job_def, default=lambda s: s.__dict__))

            # Submit the job
            job = service_client.jobs.submitJob(
                **job_def,
                _x_tapis_tenant=self.ctx.group.tenant_id,
                _x_tapis_user=self.ctx.pipeline.owner
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
                        _x_tapis_tenant=self.ctx.group.tenant_id,
                        _x_tapis_user=self.ctx.pipeline.owner
                    ).status

                job_data = {"jobUuid": job.uuid, "status": job_status}
                print("JOB DATA:", job_data)

                # Return a task result based on the final status of the tapis job
                if job_status == "FINISHED":
                    return TaskResult(0, data=job_data)

                return TaskResult(1, data=job_data)
            print("NOT POLLING TAPIS JOB")
            return TaskResult(0, data={"jobUuid": job.uuid, "status": job_status})

        except Exception as e:
            print("ERROR IN TAPIS JOB", str(e))
            return TaskResult(1, errors=[str(e)])