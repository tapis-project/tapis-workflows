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
    TaskDependency
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
        tapis_owe_templates_dir = "/tmp/git/tapis-owe-templates"
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
                    "LOCAL_INBOX_MANIFEST_PATH": {
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
                    "LOCAL_OUTBOX_SYSTEM_ID": {
                        "type": "string", 
                        "value": body.local_outbox.system_id
                    },
                    "LOCAL_OUTBOX_DATA_PATH": {
                        "type": "string",
                        "value": body.local_outbox.data_path
                    },
                    "LOCAL_OUTBOX_MANIFEST_PATH": {
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
                    "GLOBUS_SOURCE_ENDPOINT_ID": {
                        "type": "string",
                        "value": body.local_outbox.globus_endpoint_id
                    },
                    "GLOBUS_DESTINATION_ENDPOINT_ID": {
                        "type": "string",
                        "value": body.remote_inbox.globus_endpoint_id
                    },
                    "GLOBUS_DESTINATION_PATH": {
                        "type": "string",
                        "value": body.remote_inbox.globus_destination_path
                    },
                    "GLOBUS_CLIENT_ID": {
                        "type": "string",
                        "value": body.remote_inbox.globus_client_id
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

        # Create a tapis job task for each job provided in the request.
        tasks = []
        try:
            for i, job in enumerate(body.jobs, start=1):
                task_id = f"etl-job-{i}"
                tasks.append(
                    TapisJobTask(**{
                        "id": task_id,
                        "type": "tapis_job",
                        "tapis_job_def": job,
                        "depends_on": [{"id": last_task_id}]
                    })
                )
                last_task_id = task_id

            # Add the tasks from the template to the tasks list
            tasks.extend([TemplateTask(**task) for task in pipeline_template.get("tasks")])

            # Update the dependecies of the update-inbound-manifest task to
            # include the last tapis job task
            update_inbound_manifest_task = next(filter(lambda t: t.id == "update-inbound-manifest", tasks))
            update_inbound_manifest_task.depends_on.append(
                TaskDependency(id=last_task_id, can_fail=True)
            )
        except ValidationError as e:
            return BadRequest(str(e))
        
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
                return ServerErrorResp(message=e)
            except Exception as e:
                task_service.delete(tasks)
                pipeline.delete()
                return ServerErrorResp(message=e)
        return ResourceURLResponse(
            url=resource_url_builder(request.url, pipeline.id)
        )