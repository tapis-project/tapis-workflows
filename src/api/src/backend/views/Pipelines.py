from pydantic import ValidationError
from django.db import DatabaseError, IntegrityError, OperationalError
from django.forms import model_to_dict

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.errors import Conflict, BadRequest, NotFound, UnprocessableEntity, Forbidden, ServerError, MethodNotAllowed
from backend.views.http.responses.models import ModelResponse, ModelListResponse
from backend.views.http.requests import BasePipeline, CIPipeline, ImageBuildAction
from backend.models import (
    Pipeline,
    Archive,
    PipelineArchive,
    Group, GroupUser,
    ACTION_TYPE_IMAGE_BUILD
)
from backend.services import action_service, group_service
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.errors.api import BadRequestError


PIPELINE_TYPE_CI = "ci"
PIPELINE_TYPE_WORKFLOW = "workflow"
PIPELINE_TYPES = [ PIPELINE_TYPE_CI, PIPELINE_TYPE_WORKFLOW ]

PIPELINE_TYPE_MAPPING = {
    PIPELINE_TYPE_CI: "build_ci_pipeline",
    PIPELINE_TYPE_WORKFLOW: "build_workflow_pipeline"
}

class Pipelines(RestrictedAPIView):
    def get(self, request, id=None):
        # Get a list of all pipelines that belong to the user's groups
        # if no id is provided
        if id is None:
            return self.list(request)

        # Get the pipeline by the id provided in the path params
        pipeline = Pipeline.objects.filter(id=id).prefetch_related("actions").first()

        if pipeline is None:
            return NotFound(f"Pipeline not found with id '{id}'")

        # Check that the user belongs to the group that is attached
        # to this pipeline
        if not group_service.user_in_group(request.username, pipeline.group_id):
            return Forbidden(message="You do not have access to this pipeline")

        # Get the pipeline actions.
        actions = pipeline.actions.all()
        actions_result = [ model_to_dict(action) for action in actions ]

        # Convert model into a dict an
        result = model_to_dict(pipeline)
        result["actions"] = actions_result
        
        return BaseResponse(result=result)

    def list(self, request):
        # Get all the groups the user belongs to
        group_users = GroupUser.objects.filter(username=request.username)
        group_ids = [ group_user.group_id for group_user in group_users ]

        pipelines = Pipeline.objects.filter(group_id__in=group_ids)
        return ModelListResponse(pipelines)

    def post(self, request, *args, **kwargs):
        """Pipeline requests with type 'ci' are supported in order to make the 
        process of setting up a ci/cd pipeline as simple as possible. Rather than
        specifying actions, dependencies, etc, we let user pass most the required
        data in the top level of the pipeline request."""

        # Ensure the request body has a 'type' property and it is a valid value
        # before validating the rest of the request body
        if (
            "type" not in self.request_body
            or self.request_body["type"] not in PIPELINE_TYPES
        ):
            return BadRequest(f"Request body must inlcude a 'type' property with one of the following values: {PIPELINE_TYPES}")

        # Determine the proper request type. Default will be a BasePipeline request
        PipelineCreateRequest = BasePipeline
        if self.request_body["type"] == PIPELINE_TYPE_CI:
            PipelineCreateRequest = CIPipeline

        # Validate the request body based on the type of pipeline specified
        prepared_request = self.prepare(PipelineCreateRequest)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = prepared_request.body
        
        # Check that the id of the pipeline is unique
        if Pipeline.objects.filter(id=body.id).exists():
            return Conflict(f"A Pipeline already exists with the id '{body.id}'")

        # Get the group
        group = Group.objects.filter(id=body.group_id).first()

        # Check that the group_id passed by the user is a valid group
        if group is None:
            return UnprocessableEntity(f"Group '{body.group_id}' does not exist'")
    
        # Check that the user belongs to the group that is attached
        # to this pipeline
        if not group_service.user_in_group(request.username, group.id):
            return Forbidden(message="You cannot create a pipeline for this group")

        # Create the pipeline
        try:
            pipeline = Pipeline.objects.create(
                id=body.id,
                group=group,
                owner=request.username
            )
        except (IntegrityError, OperationalError) as e:
            return BadRequest(message=e.__cause__)

        # Fetch the archives specified in the request then create relations
        # between them and the pipline
        pipeline_archives = []
        try:
            # Prevent duplicate pipeline archives by casting id array to 'set'
            for archive_id in set(body.archive_ids):
                # Fetch the archive object
                archive = Archive.objects.filter(group_id=group.id, id=archive_id).first()

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

        # Fetch the function for building the pipeline according to its type.
        fn = getattr(self, PIPELINE_TYPE_MAPPING[body.type])

        return fn(body, pipeline)

    def put(self, *args, **kwargs):
        return MethodNotAllowed()

    def patch(self, *args, **kwargs):
        return MethodNotAllowed()

    def delete(self, request, id, *args, **kwargs):
        # Get the pipeline by the id provided in the path params
        pipeline = Pipeline.objects.filter(id=id).prefetch_related("actions").first()

        if pipeline is None:
            return NotFound(f"Pipeline not found with id '{id}'")

        # Delete operation only allowed by owner
        if request.username != pipeline.owner:
            return Forbidden(message="Only the owner of this pipeline can delete it")

        # Delete the pipeline
        pipeline.delete()

        # Delete the actions
        actions = pipeline.actions.all()
        for action in actions:
            action.delete()

        return BaseResponse(message=f"Pipeline '{id}' deleted. {len(actions)} action(s) deleted.")

    def build_ci_pipeline(self, body, pipeline):
        try:
            # Build an action_request from the pipeline request body
            action_request = ImageBuildAction(
                id="build",
                builder=body.builder,
                cache=body.cache,
                description="Build an image from a repository and push it to an image registry",
                destination=body.destination,
                context=body.context,
                pipeline_id=pipeline.id,
                type=ACTION_TYPE_IMAGE_BUILD
            )
        except ValidationError as e:
            pipeline.delete()
            return BadRequest(message=e)

        # Create 'build' action
        try:
            action_service.create(pipeline, action_request)
        except (IntegrityError, OperationalError) as e:
            pipeline.delete()
            return BadRequest(message=e.__cause__)
        except BadRequestError as e:
            pipeline.delete()
            return BadRequest(message=e)
        except Exception as e:
            pipeline.delete()
            return ServerError(e)

        return ModelResponse(pipeline)

    def build_workflow_pipeline(self, body, pipeline):
        # Create actions
        actions = []
        for action_request in body.actions:
            try:
                actions.append(action_service.create(pipeline, action_request))
            except (IntegrityError, OperationalError, DatabaseError) as e:
                pipeline.delete()
                return BadRequest(message=e.__cause__)
            except BadRequestError as e:
                pipeline.delete()
                return BadRequest(message=e)
            except Exception as e:
                pipeline.delete()
                return ServerError(e)

        return ModelResponse(pipeline)
