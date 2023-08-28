import json, time

from contrib.tapis.helpers import TapisServiceAPIGateway
from contrib.tapis.constants import TAPIS_JOB_POLLING_FREQUENCY, TAPIS_SYSTEM_FILE_REF_EXTENSION
from contrib.tapis.schema import ReqSubmitJob, TapisJobTaskOutput
from owe_python_sdk.TaskExecutor import TaskExecutor


class TapisJob(TaskExecutor):
    def __init__(self, task, ctx, exchange, plugins=[]):
        TaskExecutor.__init__(self, task, ctx, exchange, plugins)

    def execute(self):
        try:
            tapis_service_api_gateway = TapisServiceAPIGateway()
            service_client = tapis_service_api_gateway.get_client()

            # Recursively convert nested simple namespace objects to dict
            job_def = ReqSubmitJob(**json.loads(json.dumps(self.task.tapis_job_def, default=lambda s: dict(s))))
            
            exec_system_input_dir = job_def.execSystemInputDir
            if exec_system_input_dir == None:
                app = service_client.apps.getApp(
                    appId=job_def.appId,
                    appVersion=job_def.appVersion,
                    _x_tapis_tenant=self.ctx.params.get("tapis_tenant_id").value,
                    _x_tapis_user=self.ctx.params.get("tapis_pipeline_owner").value
                )
                exec_system_input_dir = app.jobAttributes.execSystemInputDir
                
            if exec_system_input_dir == None:
                raise Exception("Exec system input dir must be specified in either the App or the Job definition")

            # Add TapisSystemFiles from previous task output as fileInput/Arrays to the job definition
            file_input_arrays = []
            for parent_task in self.task.depends_on:
                parent_task_output = self.ctx.output[parent_task.id]
                source_urls = []
                for parent_task_output_file in parent_task_output:
                    # Skip all output files that do not contain the Tapis
                    # system file reference extension
                    if TAPIS_SYSTEM_FILE_REF_EXTENSION not in parent_task_output_file.name:
                        continue
                    
                    # Pull the Tapis System File details from the file
                    with open(parent_task_output_file.path, mode="r") as file:
                        tapis_job_task_output = TapisJobTaskOutput(**json.loads(file.read()))
                        source_urls.append(tapis_job_task_output.file.url)
                
                if len(source_urls) > 0:
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
                _x_tapis_tenant=self.ctx.params.get("tapis_tenant_id").value,
                _x_tapis_user=self.ctx.params.get("tapis_pipeline_owner").value
            )

            if self.task.poll:
                # Keep polling until the job is complete
                while job.status not in ["FINISHED", "CANCELLED", "FAILED"]:
                    # Wait the polling frequency time then try poll again
                    time.sleep(TAPIS_JOB_POLLING_FREQUENCY)
                    job = service_client.jobs.getJob(
                        jobUuid=job.uuid,
                        _x_tapis_tenant=self.ctx.params.get("tapis_tenant_id").value,
                        _x_tapis_user=self.ctx.params.get("tapis_pipeline_owner").value
                    )
                # Job has completed successfully. Get the execSystemOutputDir from the job object
                # and generate a task output for each file in the directory 
                if job.status == "FINISHED":
                    files = service_client.files.listFiles(
                        systemId=job.execSystemId,
                        path=job.execSystemOutputDir,
                        _x_tapis_tenant=self.ctx.params.get("tapis_tenant_id").value,
                        _x_tapis_user=self.ctx.params.get("tapis_pipeline_owner").value
                    )
                    for file in files:
                        self._set_output(
                            file.name + TAPIS_SYSTEM_FILE_REF_EXTENSION,
                            json.dumps(
                                TapisJobTaskOutput(
                                    exec_system_output_dir=job.execSystemOutputDir,
                                    file=file.__dict__
                                ).dict()
                            ),
                            flag="w"
                        )

                    return self._task_result(0)

                return self._task_result(1)
                
            return self._task_result(0)

        except Exception as e:
            return self._task_result(1, errors=[str(e)])