from django.db import IntegrityError
from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.errors import BaseResponse, Conflict, BadRequest, UnprocessableEntity, Forbidden, ServerError
from backend.views.http.responses.models import ModelResponse
from backend.views.http.requests import PipelineCreateRequest
from backend.models import Pipeline, Group, Context, Destination, Action
from backend.services.PipelineService import pipeline_service
from backend.services.CredentialService import CredentialService
from backend.settings import DJANGO_TAPIS_TOKEN_HEADER


class Pipelines(RestrictedAPIView):
    def post(self, request):
        # Validate the request body
        prepared_request = self.prepare(PipelineCreateRequest)

        # Return the failure view instance if validation failed
        if not prepared_request.is_valid:
            return prepared_request.failure_view

        # Get the JSON encoded body from the validation result
        body = prepared_request.body
        
        # Check that id of the pipeline is unique
        if Pipeline.objects.filter(id=body.id).exists():
            return Conflict(f"A Pipeline already exists with the id '{body['id']}'")

        # Check that the group_id passed by the user is a valid group
        if not Group.objects.filter(id=body.group_id).exists():
            return UnprocessableEntity(f"Group '{body.group_id}' does not exist'")

        # Check that the user belongs to or owns this group
        group = Group.objects.filter(id=body.group_id)[0]
        group_users = group.users.all()
        if (
            request.username != group.owner
            and request.username not in list(filter(lambda u: u.username == request.username, group_users))
        ):
            return Forbidden("You cannot create a pipeline for this group")

        # Persist the credentials for the context and destination in SK and
        # and save a ref to it in the database
        # TODO Use cicd-pipelines-svc account instead of current user's jwt
        cred_service = CredentialService(request.META[DJANGO_TAPIS_TOKEN_HEADER])

        # Create the credential for the context if one is specified
        context_cred = None
        if hasattr(body.context, "credential") and body.context.credential is not None:
            context_cred = cred_service.save(
                f"{group.id}+{body.id}+context",
                group,
                {**body.context.credential.__dict__})

        # Create the context
        try:
            context = Context.objects.save(
                branch=body.branch,
                credential=context_cred,
                type=body.type,
                url=body.url,
                visibility=body.visibility
            )
        except IntegrityError as e:
            return ServerError(message=e.__cause__)

        # Create the credential for the destination (should always be specified)
        cred_service = CredentialService(request.META[DJANGO_TAPIS_TOKEN_HEADER])
        try:
            destination_cred = cred_service.save(
                f"{group.id}+{body.id}+destination",
                group,
                {**body.destination.credential.__dict__})
        except IntegrityError as e:
            return ServerError(message=e.__cause__)

        # Create the destination
        try:
            destination = Destination.objects.save(
                credential=destination_cred,
                tag=body.tag,
                type=body.type,
                url=body.url
            )
        except IntegrityError as e:
            return ServerError(message=e.__cause__)

        # Create the pipeline
        try:
            pipeline = Pipeline.objects.create(
                id=body.id,
                auto_build=body.auto_build,
                branch=body.context.branch,
                builder=body.builder,
                context_type=body.context.type,
                destination_type=body.destination.type,
                dockerfile_path=body.context.dockerfile_path,
                group_id=body.group_id,
                image_tag=body.destination.tag,
                owner=request.username
            )
        except IntegrityError as e:
            return ServerError(message=e.__cause__)

        # Create 'build' action
        try:
            build_action = Action.objects.create(
                cache=body.cache,
                context=context,
                description="Build an image from a repository and push the image to some destination",
                destination=destination,
                http_method=None,
                name="Build",
                pipeline=pipeline,
                stage="build",
                type="container_build",
                url=None
            )
        except IntegrityError as e:
            return ServerError(message=e.__cause__)

        return ModelResponse(result=pipeline)
