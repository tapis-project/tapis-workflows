import json, time

from contrib.tapis.helpers import TapisServiceAPIGateway
from contrib.tapis.constants import TAPIS_JOB_POLLING_FREQUENCY, TAPIS_SYSTEM_FILE_REF_EXTENSION
from contrib.tapis.schema import TapisJobTaskOutput, TapisSystemFile
from owe_python_sdk.TaskExecutor import TaskExecutor


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

            # Add TapisSystemFiles from previous task output as fileInput/Arrays to the job definition
            file_input_arrays = []
            for parent_task in self.task.depends_on:
                parent_task_output = self.ctx.output[parent_task.id]
                source_urls = []
                for output_file in parent_task_output.files:
                    # Skip all output files that do not contain the Tapis
                    # system file reference extension
                    if TAPIS_SYSTEM_FILE_REF_EXTENSION not in output_file.name:
                        continue
                    
                    # Pull the Tapis System File details from the file
                    with open(output_file.path, flag="r") as file:
                        tapis_system_file = TapisSystemFile(json.loads(file.read())["file"])
                        if tapis_system_file.type == "file":
                            source_urls.append(tapis_system_file.url)
                
                file_input_arrays.append({
                    "name": f"owe-implicit-input-{parent_task.id}",
                    "description": f"These files were generated as a result of a Tapis Job submission via an Open Workflow Engine task execution for the pipeline '{self.ctx.pipeline.id}' and task '{parent_task.id}'.",
                    "sourceUrls": source_urls,
                    "targetDir": "*",
                    "notes": {}
                })

            # Add the file input arrays to the Tapis Job definition
            if job_def.get("fileInputArrays", None) == None:
                job_def["fileInputArrays"] = []

            job_def["fileInputArrays"].extend(file_input_arrays)

            # Submit the job
            job = service_client.jobs.submitJob(
                **job_def,
                _x_tapis_tenant=self.ctx.params.tapis_tenant_id,
                _x_tapis_user=self.ctx.params.tapis_pipeline_owner
            )

            if self.task.poll:
                # Keep polling until the job is complete
                while job.status not in ["FINISHED", "CANCELLED", "FAILED"]:
                    # Wait the polling frequency time then try poll again
                    time.sleep(TAPIS_JOB_POLLING_FREQUENCY)
                    job = service_client.jobs.getJob(
                        jobUuid=job.uuid,
                        _x_tapis_tenant=self.ctx.params.tapis_tenant_id,
                        _x_tapis_user=self.ctx.params.tapis_pipeline_owner
                    )

                # Job has completed successfully. Get the execSystemOutputDir from the job object
                # and generate a task output for each file in the directory 
                if job.status == "FINISHED":
                    files = service_client.files.listFiles(systemId=job.execSystemId, path=job.execSystemOutputDir)
                    for _file in files:
                        self._set_output(
                            _file.name + TAPIS_SYSTEM_FILE_REF_EXTENSION,
                            json.dumps(TapisJobTaskOutput(system_id=job.execSystemId, file=_file).dict())
                        )

                    return self._task_result(0)

                return self._task_result(1)
                
            return self._task_result(0)

        except Exception as e:
            self.ctx.logger.error(f"ERROR IN TAPIS JOB: {str(e)}")
            return self._task_result(1, errors=[str(e)])