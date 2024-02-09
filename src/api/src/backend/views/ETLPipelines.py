import os, json

import git

from pydantic import ValidationError
from django.db import DatabaseError, IntegrityError, OperationalError

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.errors import (
    Conflict,
    BadRequest,
    NotFound,
    Forbidden,
    ServerError as ServerErrorResp,
    UnprocessableEntity
)
from backend.views.http.responses import ResourceURLResponse
from backend.views.http.requests import (
    Uses,
    TemplateTask,
    TapisJobTask,
    TaskDependency,
    TaskInputSpec
)
from backend.views.http.etl import TapisETLPipeline
from backend.models import (
    Pipeline as PipelineModel,
    Archive,
    PipelineArchive
)
from backend.services.TaskService import service as task_service
from backend.services.GroupService import service as group_service
from backend.errors.api import BadRequestError, ServerError
from backend.helpers import resource_url_builder
from backend.conf.constants import (
    LATEST_TAPIS_ETL_PIPELINE_TEMPLATE_NAME,
    TAPIS_ETL_TEMPLATE_REPO_BRANCH,
    TAPIS_ETL_TEMPLATE_REPO_URL
)


class ETLPipelines(RestrictedAPIView):
    def post(self, request, group_id, *_, **__):
        """ETL Pipelines"""
        # Get the group
        group = group_service.get(group_id, request.tenant_id)
        if group == None:
            return NotFound(f"No group found with id '{group_id}'")

        # Check that the user belongs to the group
        if not group_service.user_in_group(request.username, group_id, request.tenant_id):
            return Forbidden(message="You do not have access to this group")
        
        # Git repository that contains the pipeline and task definitions for the
        # tapis etl pipeline
        uses = Uses(**{
            "name": LATEST_TAPIS_ETL_PIPELINE_TEMPLATE_NAME,
            "source": {
                "url": TAPIS_ETL_TEMPLATE_REPO_URL,
                "branch": TAPIS_ETL_TEMPLATE_REPO_BRANCH
            }
        })
        
        # Validate the request body based on the type of pipeline specified
        prepared_request = self.prepare(
            TapisETLPipeline,
            uses=uses
        )
        
        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view
        
        # Get the JSON encoded body from the validation result
        body = prepared_request.body
        
        # Check that the id of the pipeline is unique
        if PipelineModel.objects.filter(id=body.id, group=group).exists():
            return Conflict(f"A Pipeline already exists with the id '{body.id}'")
        
        # Clone the git repository that contains the pipeline and task definitions that will be used
        tapis_owe_templates_dir = "/tmp/git/tapis-workflows-task-templates"
        cloned = os.path.exists(tapis_owe_templates_dir)
        if not cloned:
            try:
                git.Repo.clone_from(
                    uses.source.url,
                    tapis_owe_templates_dir
                )
            except Exception as e:
                return ServerErrorResp(f"Error cloning the Tapis OWE Template repository: {str(e)}")
            
        # A local tapis owe templates repo exists, update it with a git pull
        git.cmd.Git(tapis_owe_templates_dir).pull()
        
        try:
            # Open the owe-config.json file
            with open(os.path.join(tapis_owe_templates_dir, "owe-config.json")) as file:
                owe_config = json.loads(file.read())

            # Open the etl pipeline schema.json
            with open(
                os.path.join(
                    tapis_owe_templates_dir,
                    owe_config.get(LATEST_TAPIS_ETL_PIPELINE_TEMPLATE_NAME).get("path")
                )
            ) as file:
                pipeline_template = json.loads(file.read())
        except Exception as e:
            return UnprocessableEntity(f"Configuration Error (owe-config.json): {str(e)}")

        # Create the pipeline
        try:
            # Convert the data integrity policies to dicts. Easier
            # to handle for null values via .get
            inbox_data_integrity_profile = {}
            if getattr(body.local_inbox, "data_integrity_profile", None) != None:
                inbox_data_integrity_profile = body.local_inbox.data_integrity_profile.dict()
            

            outbox_data_integrity_profile = {}
            if getattr(body.local_outbox, "data_integrity_profile", None) != None:
                outbox_data_integrity_profile = body.local_outbox.data_integrity_profile.dict()

            pipeline = PipelineModel.objects.create(
                id=body.id,
                description=getattr(body, "description", None) or pipeline_template.get("description"),
                group=group,
                owner=request.username,
                # Here we are using the execution profile provided in the request, but
                # overwritting the 'duplicate_submission_policy' defined in the
                # the pipeline template.
                **{
                    **body.execution_profile.dict(),
                    "duplicate_submission_policy": pipeline_template
                        .get("execution_profile")
                        .get("duplicate_submission_policy")
                },
                env={
                    **pipeline_template.get("env"),
                    "LOCAL_INBOX_SYSTEM_ID": {
                        "type": "string",
                        "value": body.local_inbox.system_id
                    },
                    "LOCAL_INBOX_DATA_PATH": {
                        "type": "string",
                        "value": body.local_inbox.data_path
                    },
                    "LOCAL_INBOX_INCLUDE_PATTERN": {
                        "type": "string",
                        "value": body.local_inbox.include_pattern
                    },
                    "LOCAL_INBOX_EXCLUDE_PATTERN": {
                        "type": "string",
                        "value": body.local_inbox.exclude_pattern
                    },
                    "LOCAL_INBOX_MANIFESTS_PATH": {
                        "type": "string",
                        "value": body.local_inbox.manifests_path
                    },
                    "LOCAL_INBOX_MANIFEST_GENERATION_POLICY": {
                        "type": "string",
                        "value": body.local_inbox.manifest_generation_policy
                    },
                    "LOCAL_INBOX_MANIFEST_PRIORITY": {
                        "type": "string",
                        "value": body.local_inbox.manifest_priority
                    },
                    "LOCAL_INBOX_DATA_INTEGRITY_TYPE": {
                        "type": "string",
                        "value": inbox_data_integrity_profile.get(
                            "type",
                            None
                        )
                    },
                    "LOCAL_INBOX_DATA_INTEGRITY_DONE_FILES_PATH": {
                        "type": "string",
                        "value": inbox_data_integrity_profile.get(
                            "done_files_path",
                            None
                        )
                    },
                    "LOCAL_INBOX_DATA_INTEGRITY_DONE_FILE_INCLUDE_PATTERN": {
                        "type": "string",
                        "value": inbox_data_integrity_profile.get(
                            "include_pattern",
                            None
                        )
                    },
                    "LOCAL_INBOX_DATA_INTEGRITY_DONE_FILE_EXCLUDE_PATTERN": {
                        "type": "string",
                        "value": inbox_data_integrity_profile.get(
                            "exclude_pattern",
                            None
                        )
                    },
                    "LOCAL_OUTBOX_SYSTEM_ID": {
                        "type": "string",
                        "value": body.local_outbox.system_id
                    },
                    "LOCAL_OUTBOX_DATA_PATH": {
                        "type": "string",
                        "value": body.local_outbox.data_path
                    },
                    "LOCAL_OUTBOX_INCLUDE_PATTERN": {
                        "type": "string",
                        "value": body.local_outbox.include_pattern
                    },
                    "LOCAL_OUTBOX_EXCLUDE_PATTERN": {
                        "type": "string",
                        "value": body.local_outbox.exclude_pattern
                    },
                    "LOCAL_OUTBOX_MANIFESTS_PATH": {
                        "type": "string",
                        "value": body.local_outbox.manifests_path
                    },
                    "LOCAL_OUTBOX_MANIFEST_GENERATION_POLICY": {
                        "type": "string",
                        "value": body.local_outbox.manifest_generation_policy
                    },
                    "LOCAL_OUTBOX_MANIFEST_PRIORITY": {
                        "type": "string",
                        "value": body.local_outbox.manifest_priority
                    },
                    "LOCAL_OUTBOX_DATA_INTEGRITY_TYPE": {
                        "type": "string",
                        "value": outbox_data_integrity_profile.get(
                            "type",
                            None
                        )
                    },
                    "LOCAL_OUTBOX_DATA_INTEGRITY_DONE_FILES_PATH": {
                        "type": "string",
                        "value": outbox_data_integrity_profile.get(
                            "done_files_path",
                            None
                        )
                    },
                    "LOCAL_OUTBOX_DATA_INTEGRITY_DONE_FILE_INCLUDE_PATTERN": {
                        "type": "string",
                        "value": outbox_data_integrity_profile.get(
                            "include_pattern",
                            None
                        )
                    },
                    "LOCAL_OUTBOX_DATA_INTEGRITY_DONE_FILE_EXCLUDE_PATTERN": {
                        "type": "string",
                        "value": outbox_data_integrity_profile.get(
                            "exclude_pattern",
                            None
                        )
                    },
                    "REMOTE_INBOX_PATH": {
                        "type": "string",
                        "value": body.remote_inbox.path
                    },
                    "REMOTE_INBOX_SYSTEM_ID": {
                        "type": "string",
                        "value": body.remote_inbox.system_id
                    }
                },
                params=pipeline_template.get("params", {})
            )
        except (IntegrityError, OperationalError) as e:
            return BadRequest(message=e.__cause__)
        except Exception as e:
            return ServerErrorResp(f"{e}")

        # Fetch the archives specified in the request then create relations
        # between them and the pipline
        pipeline_archives = []
        try:
            # Prevent duplicate pipeline archives by casting id array to 'set'
            for archive_id in set(body.archive_ids):
                # Fetch the archive object
                archive = Archive.objects.filter(group=group, id=archive_id).first()

                # Return bad request if archive not found
                if archive == None:
                    pipeline.delete()
                    return BadRequest(message=f"Archive not found with an id of '{archive_id}' and group_id '{group.id}'")
        
                pipeline_archives.append(
                    PipelineArchive.objects.create(
                        pipeline=pipeline,
                        archive=archive
                    )
                )
        except (IntegrityError, OperationalError, DatabaseError) as e:
            # Delete the pipeline
            pipeline.delete()

            # Delete the pipeline archive relationships that were just created
            [pipeline_archive.delete() for pipeline_archive in pipeline_archives]
            return BadRequest(message=e.__cause__)
        
        # The first tapis job should be dependent on the gen-inbound-manifests task
        last_task_id = "gen-inbound-manifests"

        # No-op condition
        # Create a condition that should only be applied to the first Tapis Job
        # in the series to ensure that when there is no data to process, the first
        # job (and all subsequent jobs) do not run
        no_op_condition = {
            "ne": [
                {
                    "task_output": {
                        "task_id": last_task_id,
                        "output_id": "ACTIVE_MANIFEST"
                    }
                },
                "null"
            ]
        }

        # Create a tapis job task for each job provided in the request.
        tasks = []
        job_tasks = []
        try:
            for i, job in enumerate(body.jobs, start=1):
                # Set up the conditions for the job to run
                conditions = [
                    {
                        "eq": [
                            {"args": "RESUBMIT_OUTBOUND"},
                            None
                        ]
                    }
                ]
                
                # Add no-op condition for only first task
                if i == 1:
                    conditions.append(no_op_condition)

                task_id = f"etl_job_{i}"
                tapis_job_task = TapisJobTask(**{
                        "id": task_id,
                        "type": "tapis_job",
                        "tapis_job_def": job,
                        "depends_on": [{"id": last_task_id}],
                        "conditions": conditions
                    })
                tasks.append(tapis_job_task)
                job_tasks.append(tapis_job_task)
                last_task_id = task_id

            # Add the tasks from the template to the tasks list
            tasks.extend([TemplateTask(**task) for task in pipeline_template.get("tasks")])

            # Update the dependecies of the inbound-status-reduce task to
            # include all tapis-job tasks
            status_reduce_task = next(filter(lambda t: t.id == "inbound-status-reduce", tasks))
            for job_task in job_tasks:
                status_reduce_task.depends_on.append(
                    TaskDependency(id=job_task.id, can_fail=True)
                )

                status_reduce_task.input[f"{job_task.id}_JOB_STATUS"] = TaskInputSpec(
                    value_from={
                        "task_output": {
                            "task_id": job_task.id,
                            "output_id": "STATUS"
                        }
                    }
                )
        except ValidationError as e:
            # Delete the pipeline
            pipeline.delete()
            return BadRequest(str(e))
        except Exception as e:
            # Delete the pipeline
            pipeline.delete()
            return ServerErrorResp(str(e))
        
        # Add the tasks to the database
        for task in tasks:
            try:
                task_service.create(pipeline, task)
            except (ValidationError, BadRequestError) as e:
                pipeline.delete()
                task_service.delete(tasks)
                return BadRequest(message=e)
            except (IntegrityError, OperationalError, DatabaseError) as e:
                pipeline.delete()
                task_service.delete(tasks)
                return BadRequest(message=e.__cause__)
            except ServerError as e:
                pipeline.delete()
                task_service.delete(tasks)
                return ServerErrorResp(message=e)
            except Exception as e:
                pipeline.delete()
                task_service.delete(tasks)
                return ServerErrorResp(message=e)
        return ResourceURLResponse(
            url=resource_url_builder(request.url, pipeline.id)
        )