from time import time

from tapipy.tapis import Tapis

from core.ActionResult import ActionResult
from conf.configs import TAPIS_SERVICE_ACCOUNT, TAPIS_SERVICE_ACCOUNT_PASSWORD, TAPIS_BASE_URL, TAPIS_JOB_POLLING_FREQUENCY


class TapisJob:
    def execute(self, action, _):
        try:
            client = Tapis(
                base_url=TAPIS_BASE_URL,
                username=TAPIS_SERVICE_ACCOUNT,
                password=TAPIS_SERVICE_ACCOUNT_PASSWORD
            )
            
            # TODO Cache the jwt
            client.get_tokens()

            # Submit the job
            job = client.jobs.submitJob(**action.tapis_job_def)

            # Get the initial job status
            job_status = job.status

            if action.poll:
                # Keep polling until the job is complete
                while job_status not in [ "FINISHED", "CANCELLED", "FAILED" ]:
                    # Wait the polling frequency time then try poll again
                    time.sleep(TAPIS_JOB_POLLING_FREQUENCY)
                    job_status = client.jobs.getJobStatus(jobUuid=job.uuid).status

                job_data = {"jobUuid": job.uuid, "status": job_status}

                # Return an action result based on the final status of the tapis job
                if job_status == "FINISHED":
                    return ActionResult(0, data=job_data)

                return ActionResult(1, data=job_data)

            return ActionResult(0, data={"jobUuid": job.uuid, "status": job_status})

        except Exception as e:
            return ActionResult(1, errors=[str(e)])

executor = TapisJob()