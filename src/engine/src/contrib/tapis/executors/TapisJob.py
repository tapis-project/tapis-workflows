import json, time

from contrib.tapis.helpers import TapisServiceAPIGateway
from contrib.tapis.constants import TAPIS_JOB_POLLING_FREQUENCY, TAPIS_SYSTEM_FILE_REF_EXTENSION
from contrib.tapis.schema import TapisJob, TapisJobTaskOutput, TapisSystemFile
from owe_python_sdk.TaskExecutor import TaskExecutor


class TapisJob(TaskExecutor):
    def __init__(self, task, ctx, exchange):
        TaskExecutor.__init__(self, task, ctx, exchange)

    def execute(self):
        try:
            tapis_service_api_gateway = TapisServiceAPIGateway()
            service_client = tapis_service_api_gateway.get_client()

            # Recursively convert nested simple namespace objects to dict
            job_def = TapisJob(**json.loads(json.dumps(self.task.tapis_job_def, default=lambda s: dict(s))))

            # Get the execSystemId from the job def if specified. If not, get the execSystemId from
            # the app
            exec_system_id = job_def.execSystemId
            if exec_system_id == None:
                app = service_client.apps.getApp(
                    appId=job_def.appId,
                    appVersion=job_def.appVersion,
                    _x_tapis_tenant=self.ctx.params.tapis_tenant_id,
                    _x_tapis_user=self.ctx.params.tapis_pipeline_owner
                )

                exec_system_id = app.jobAttributes.execSystemId

            if exec_system_id == None:
                raise Exception("Exec system id must be specified in either the App or the Job definition")
            
            exec_system_input_dir = job_def.execSystemInputDir
            if exec_system_input_dir == None:
                exec_system_input_dir = app.jobAttributes.exec_system_input_dir

            if exec_system_input_dir == None:
                raise Exception("Exec system input dir must be specified in either the App or the Job definition")

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
                        tapis_job_task_output = TapisJobTaskOutput(**json.loads(file.read()))
                        source_urls.append(tapis_job_task_output.file.url)
                
                file_input_arrays.append({
                    "name": f"owe-implicit-input-{parent_task.id}",
                    "description": f"These files were generated as a result of a Tapis Job submission via an Open Workflow Engine task execution for the pipeline '{self.ctx.pipeline.id}' and task '{parent_task.id}'.",
                    "sourceUrls": source_urls,
                    "targetDir": exec_system_input_dir,
                    "notes": {}
                })

            # Add the file input arrays to the Tapis Job definition
            job_def.fileInputArrays.extend(file_input_arrays)

            # Submit the job
            job = service_client.jobs.submitJob(
                **job_def.dict(),
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
                            json.dumps(
                                TapisJobTaskOutput(
                                    exec_system_output_dir=job.execSystemOutputDir,
                                    file=_file
                                ).dict()
                            )
                        )

                    return self._task_result(0)

                return self._task_result(1)
                
            return self._task_result(0)

        except Exception as e:
            self.ctx.logger.error(f"ERROR IN TAPIS JOB: {str(e)}")
            return self._task_result(1, errors=[str(e)])