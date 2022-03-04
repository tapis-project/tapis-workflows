from django.db import IntegrityError, OperationalError
from django.forms import model_to_dict

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.errors import Conflict, BadRequest, NotFound, UnprocessableEntity, Forbidden
from backend.views.http.responses.models import ModelResponse, ModelListResponse
from backend.views.http.requests import BasePipeline, CIPipeline
from backend.models import Pipeline, Group, Context, Destination, Action, Context, Destination, GroupUser, PIPELINE_TYPES, PIPELINE_TYPE_CI, PIPELINE_TYPE_WORKFLOW
from backend.services.CredentialService import cred_service
from backend.views.http.responses.BaseResponse import BaseResponse


class Pipelines(RestrictedAPIView):
    BaseResponse
    def get(self, request, id=None):
        # Get all the groups the user belongs to
        group_users = GroupUser.objects.filter(username=request.username)
        group_ids = [ group_user.group_id for group_user in group_users ]

        # Get a list of all pipelines if id is not set
        if id is None:
            pipelines = Pipeline.objects.filter(group_id__in=group_ids)
            return ModelListResponse(pipelines)

        # Return the pipeline by the id provided in the path params
        pipeline = Pipeline.objects.filter(id=id).prefetch_related(
            "actions",
            "actions__context",
            "actions__context__credential",
            "actions__destination",
            "actions__destination__credential"
        ).first()

        if pipeline is None:
            return NotFound(f"Pipeline not found with id '{id}'")

        # Check that the user belongs to the group that is attached
        # to this pipline
        if pipeline.group_id not in group_ids:
            return Forbidden(message="You do not have access to this pipeline")

        # Get the pipeline actions.
        actions = pipeline.actions.all()
        actions_result = []
        for action in actions:
            action_result = model_to_dict(action)

            action_result["context"] = model_to_dict(action.context)
            if action.context.credential is not None:
                action_result["context"]["credential"] = model_to_dict(action.context.credential)

            action_result["destination"] = model_to_dict(action.destination)
            action_result["destination"]["credential"] = model_to_dict(action.destination.credential)

            actions_result.append(action_result)

        # Convert model into a dict an
        result = model_to_dict(pipeline)
        result["actions"] = actions_result
        
        return BaseResponse(result=result)

    def post(self, request, **_):
        # Ensure the request body has a 'type' property and it is a valid value
        # before validating the rest of the request body
        pipeline_types = [ptype[0] for ptype in PIPELINE_TYPES]
        if (
            "type" not in self.request_body
            or self.request_body["type"] not in pipeline_types
        ):
            return BadRequest(f"Request body must inlcude a 'type' property with one of the following values: {pipeline_types}")

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
        
        # Check that id of the pipeline is unique
        if Pipeline.objects.filter(id=body.id).exists():
            return Conflict(f"A Pipeline already exists with the id '{body.id}'")

        # Get the group
        group = Group.objects.filter(id=body.group_id).first()

        # Check that the group_id passed by the user is a valid group
        if group is None:
            return UnprocessableEntity(f"Group '{body.group_id}' does not exist'")

        # Get all the groups the user belongs to
        group_users = GroupUser.objects.filter(username=request.username)
        group_ids = [ group_user.group_id for group_user in group_users ]

        # Check that the user belongs to the group that is attached
        # to this pipline
        if body.group_id not in group_ids:
            return Forbidden(message="You cannot create a pipeline for this group")

        # NOTE Pipeline requests with type 'ci' are supported in order to make the 
        # process of setting up a ci pipeline as simple as possible. Rather than
        # specifying actions, dependencies, etc, we let user pass most the required
        # data in the top level of the pipline request.
        if body.type == PIPELINE_TYPE_CI:
            return self.build_ci_pipline(body, group, request.username)

        return self.build_workflow_pipeline()

    def build_ci_pipline(self, body, group, owner):
        # Persist the credentials for the context and destination in SK and
        # and save a ref to it in the database
        # Create the credential for the context if one is specified
        context_cred = None
        if hasattr(body.context, "credential") and body.context.credential is not None:
            context_cred_data = {}
            for key, value in dict(body.context.credential).items():
                if value is not None:
                    context_cred_data[key] = getattr(body.context.credential, key)
            
            try:
                context_cred = cred_service.save(
                    f"{group.id}+{body.id}+context",
                    group,
                    context_cred_data
                )
            except (IntegrityError, OperationalError) as e:
                return BadRequest(message=e.__cause__)

        # Create the context
        try:
            context = Context.objects.create(
                branch=body.context.branch,
                credential=context_cred,
                dockerfile_path=body.context.dockerfile_path,
                sub_path=body.context.sub_path,
                type=body.context.type,
                url=body.context.url,
                visibility=body.context.visibility
            )
        except (IntegrityError, OperationalError) as e:
            cred_service.delete(context_cred.sk_id)
            return BadRequest(message=e.__cause__)

        # Create the credential for the destination (should always be specified)

        destination_cred_data = {}
        for key, value in dict(body.destination.credential).items():
            if value is not None:
                destination_cred_data[key] = getattr(body.destination.credential, key)
        try:
            destination_cred = cred_service.save(
                f"{group.id}+{body.id}+destination",
                group,
                destination_cred_data
            )
        except (IntegrityError, OperationalError) as e:
            cred_service.delete(context_cred.sk_id)
            context.delete()
            return BadRequest(message=e.__cause__)

        # Create the destination
        try:
            destination = Destination.objects.create(
                credential=destination_cred,
                tag=body.destination.tag,
                type=body.destination.type,
                url=body.destination.url
            )
        except (IntegrityError, OperationalError) as e:
            cred_service.delete(context_cred.sk_id)
            context.delete()
            cred_service.delete(destination_cred.sk_id)
            return BadRequest(message=e.__cause__)

        # Create the pipeline
        try:
            pipeline = Pipeline.objects.create(
                id=body.id,
                auto_build=body.auto_build,
                branch=body.context.branch,
                builder=body.builder,
                context_url=body.context.url,
                context_sub_path=body.context.sub_path,
                context_type=body.context.type,
                destination_type=body.destination.type,
                dockerfile_path=body.context.dockerfile_path,
                group_id=body.group_id,
                image_tag=body.destination.tag,
                owner=owner
            )
        except (IntegrityError, OperationalError) as e:
            cred_service.delete(context_cred.sk_id)
            context.delete()
            cred_service.delete(destination_cred.sk_id)
            destination.delete()
            return BadRequest(message=e.__cause__)

        # Create 'build' action
        try:
            Action.objects.create(
                builder=pipeline.builder,
                cache=body.cache,
                context=context,
                description="Build an image from a repository and push it to an image registry",
                destination=destination,
                http_method=None,
                name="image_build",
                pipeline=pipeline,
                type="image_build",
                url=None
            )
        except (IntegrityError, OperationalError) as e:
            cred_service.delete(context_cred.sk_id)
            context.delete()
            cred_service.delete(destination_cred.sk_id)
            destination.delete()
            pipeline.delete()
            return BadRequest(message=e.__cause__)

        return ModelResponse(pipeline)

    def build_workflow_pipeline(self):
        return BaseResponse(message="workflow")
