from time import time

from tapipy.tapis import Tapis

from core.tasks.TaskResult import TaskResult
from conf.constants import (
    TAPIS_SERVICE_ACCOUNT,
    TAPIS_SERVICE_ACCOUNT_PASSWORD,
    TAPIS_DEV_URL,
    TAPIS_JOB_POLLING_FREQUENCY,
)


class TapisJob:
    def execute(self, task):
        try:
            client = Tapis(
                base_url=TAPIS_DEV_URL,
                username=TAPIS_SERVICE_ACCOUNT,
                password=TAPIS_SERVICE_ACCOUNT_PASSWORD,
            )

            # TODO Cache the jwt
            client.get_tokens()

            # Submit the job
            job = client.jobs.submitJob(**task.tapis_job_def)

            # Get the initial job status
            job_status = job.status

            if task.poll:
                # Keep polling until the job is complete
                while job_status not in ["FINISHED", "CANCELLED", "FAILED"]:
                    # Wait the polling frequency time then try poll again
                    time.sleep(TAPIS_JOB_POLLING_FREQUENCY)
                    job_status = client.jobs.getJobStatus(jobUuid=job.uuid).status

                job_data = {"jobUuid": job.uuid, "status": job_status}

                # Return a task result based on the final status of the tapis job
                if job_status == "FINISHED":
                    return TaskResult(0, data=job_data)

                return TaskResult(1, data=job_data)

            return TaskResult(0, data={"jobUuid": job.uuid, "status": job_status})

        except Exception as e:
            return TaskResult(1, errors=[str(e)])


executor = TapisJob()
