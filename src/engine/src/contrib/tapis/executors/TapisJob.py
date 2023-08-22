import json, time

from contrib.tapis.helpers import TapisServiceAPIGateway
from contrib.tapis.constants import TAPIS_JOB_POLLING_FREQUENCY
from contrib.tapis.schema import TapisJobTaskOutput

from core.tasks.TaskExecutor import TaskExecutor


class TapisJob(TaskExecutor):
    def __init__(self, task, ctx, exchange):
        TaskExecutor.__init__(self, task, ctx, exchange)

    def execute(self):
        try:
            tapis_service_api_gateway = TapisServiceAPIGateway()
            service_client = tapis_service_api_gateway.get_client()

            # Recursively convert nested simple namespace objects to dict
            job_def = json.loads(json.dumps(self.task.tapis_job_def, default=lambda s: dict(s)))

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

                # Job has completed successfully. Get the execSystemOutputDir from the job object
                # and generate a task output for each file in the directory 
                if job_status == "FINISHED":
                    job = service_client.jobs.getJob(
                        jobUuid=job.uuid,
                        _x_tapis_tenant=self.ctx.params.tapis_tenant_id,
                        _x_tapis_user=self.ctx.params.tapis_pipeline_owner
                    )

                    files = service_client.files.listFiles(systemId=job.execSystemId, path=job.execSystemOutputDir)
                    for _file in files:
                        self._set_output(
                            _file.name,
                            json.dumps(TapisJobTaskOutput(file=_file).dict())
                        )

                    return self._task_result(0)

                return self._task_result(1)
                
            return self._task_result(0)

        except Exception as e:
            self.ctx.logger.error(f"ERROR IN TAPIS JOB: {str(e)}")
            return self._task_result(1, errors=[str(e)])