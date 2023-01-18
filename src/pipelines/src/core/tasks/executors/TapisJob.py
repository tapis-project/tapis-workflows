from time import time

from helpers.TapisServiceAPIGateway import TapisServiceAPIGateway

from core.tasks.TaskResult import TaskResult
from conf.constants import TAPIS_JOB_POLLING_FREQUENCY


class TapisJob:
    def execute(self, task):
        try:
            tapis_service_api_gateway = TapisServiceAPIGateway()
            service_client = tapis_service_api_gateway.get_client()

            # Submit the job
            job = service_client.jobs.submitJob(**task.tapis_job_def)

            # Get the initial job status
            job_status = job.status

            if task.poll:
                # Keep polling until the job is complete
                while job_status not in ["FINISHED", "CANCELLED", "FAILED"]:
                    # Wait the polling frequency time then try poll again
                    time.sleep(TAPIS_JOB_POLLING_FREQUENCY)
                    job_status = service_client.jobs.getJobStatus(jobUuid=job.uuid).status

                job_data = {"jobUuid": job.uuid, "status": job_status}

                # Return a task result based on the final status of the tapis job
                if job_status == "FINISHED":
                    return TaskResult(0, data=job_data)

                return TaskResult(1, data=job_data)

            return TaskResult(0, data={"jobUuid": job.uuid, "status": job_status})

        except Exception as e:
            return TaskResult(1, errors=[str(e)])


executor = TapisJob()
