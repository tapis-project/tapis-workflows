from typing import List
from pydantic import ValidationError
from django.db import DatabaseError, IntegrityError, OperationalError
from django.forms import model_to_dict

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.errors import (
    Conflict,
    BadRequest,
    NotFound,
    Forbidden,
    ServerError as ServerErrorResp
)
from backend.views.http.responses import BaseResponse, ResourceURLResponse
from backend.views.http.requests import ImageBuildTask
from backend.views.http.etl import TapisETLPipeline
from backend.models import (
    Pipeline as PipelineModel,
    Archive,
    PipelineArchive,
    TASK_TYPE_IMAGE_BUILD
)
from backend.services.TaskService import service as task_service
from backend.services.GroupService import service as group_service
from backend.errors.api import BadRequestError, ServerError
from backend.helpers import resource_url_builder


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

        # Validate the request body based on the type of pipeline specified
        prepared_request = self.prepare(
            TapisETLPipeline,
            uses={
                "name": "tapis/etl-pipeline@v1beta",
                "source": {
                    "url": "https://github.com/tapis-project/tapis-owe-templates.git",
                    "branch": "master"
                }
            }
        )

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = prepared_request.body
        
        # Check that the id of the pipeline is unique
        if PipelineModel.objects.filter(id=body.id, group=group).exists():
            return Conflict(f"A Pipeline already exists with the id '{body.id}'")

        # Create the pipeline
        try:
            pipeline = PipelineModel.objects.create(
                id=body.id,
                group=group,
                owner=request.username,
                max_exec_time=body.execution_profile.max_exec_time,
                invocation_mode=body.execution_profile.invocation_mode,
                max_retries=body.execution_profile.max_retries,
                retry_policy=body.execution_profile.retry_policy,
                duplicate_submission_policy=body.execution_profile.duplicate_submission_policy,
                env=body.dict()["env"],
                params=body.dict()["params"]
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


        return fn(request, body, pipeline)

    def build_ci_pipeline(self, request, body, pipeline):
        try:
            # Build an task_request from the pipeline request body
            task_request = ImageBuildTask(
                id="build",
                builder=body.builder,
                cache=body.cache,
                description="Build an image from a repository and push it to an image registry",
                destination=body.destination,
                context=body.context,
                pipeline_id=pipeline.id,
                type=TASK_TYPE_IMAGE_BUILD
            )

            # Create 'build' task
            task_service.create(pipeline, task_request)
        except (ValidationError, BadRequestError) as e:
            pipeline.delete()
            return BadRequest(message=e)
        except (IntegrityError, OperationalError, DatabaseError) as e:
            pipeline.delete()
            return BadRequest(message=e.__cause__)
        except Exception as e:
            pipeline.delete()
            return ServerErrorResp(message=e)

        return ResourceURLResponse(
            url=resource_url_builder(request.url.replace("/ci", "/pipelines"), pipeline.id))

    def build_workflow_pipeline(self, request, body, pipeline):
        # Create tasks
        # TODO Use the TaskService to delete Tasks so it can delete
        # all the secrets/credentials associated with it
        tasks = []
        for task_request in body.tasks:
            try:
                tasks.append(task_service.create(pipeline, task_request))
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
            url=resource_url_builder(request.url, pipeline.id))
