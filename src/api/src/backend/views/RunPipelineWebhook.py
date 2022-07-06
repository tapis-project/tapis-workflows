from django.db import IntegrityError, DatabaseError, OperationalError

from backend.views.APIView import APIView
from backend.views.http.requests import WebhookEvent
from backend.views.http.responses.models import ModelResponse
from backend.views.http.responses.errors import ServerError as ServerErrorResp
from backend.services.PipelineDispatcher import service as pipeline_dispatcher
from backend.services.CredentialsService import service as cred_service
from backend.models import Identity, Event, Pipeline, Group, GroupUser
from backend.helpers.PipelineDispatchRequestBuilder import PipelineDispatchRequestBuilder
from backend.errors.api import ServerError


WEBHOOK_SOURCE_GITHUB = "github"
WEBHOOK_SOURCE_GITLAB = "gitlab"
WEBHOOK_SOURCES = [WEBHOOK_SOURCE_GITHUB, WEBHOOK_SOURCE_GITLAB]

request_builder = PipelineDispatchRequestBuilder(cred_service)

class RunPipelineWebhook(APIView):
    def post(self, _, group_id, pipeline_id):
        prepared_request = self.prepare(WebhookEvent)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

        # Get the group for this request
        group = Group.objects.filter(id=group_id).first()

        # Return Event if group does not exist
        if group == None:
            event = self._create_event(
                body,
                group,
                None,
                f"Pipeline failed to run. Group '{group_id}' does not exist"
            )
            return ModelResponse(event)

        # Find a pipeline that matches the request data
        pipeline = Pipeline.objects.filter(
            id=pipeline_id,
            group_id=group_id
        ).prefetch_related(
            "group",
            "archives",
            "archives__archive",
            "actions",
            "actions__context",
            "actions__context__credentials",
            "actions__context__identity",
            "actions__destination",
            "actions__destination__credentials",
            "actions__destination__identity",
        ).first()

        # Return event if pipeline does not exist
        if pipeline == None:
            event = self._create_event(
                body,
                group,
                pipeline,
                f"Pipeline failed to run. Pipeline '{pipeline_id}' does not exist"
            )
            return ModelResponse(event)

        # Ensure the identity of the user triggering the pipeline is
        # authorized to do so
        group_users = GroupUser.objects.filter(group=group)
        
        identities = []
        for group_user in group_users:
            identities = identities + list(
                Identity.objects.filter(
                    owner=group_user.username,
                    type=body.source
                ).prefetch_related("credentials")
            )

        # If an identity is found with the username provided in the 
        # webhook notification, this pipeline can be dispatched
        username = None
        for identity in identities: 
            # Fetch the secret from SK
            secret = cred_service.get_secret(identity.credentials.sk_id)
            if secret == None: break

            # Get the username from the secret
            identity_username = secret.get("username")
            if identity_username == None: break

            if identity_username and identity_username == body.username:
                username = identity_username
                break

        if username == None:
            event = self._create_event(
                body,
                group,
                pipeline,
                f"Pipeline failed to run. No identity found with type '{body.source}' and username '{body.username}'"
            )
            return ModelResponse(event)

        # Create the event
        try:
            event = self._create_event(
                body,
                group,
                pipeline,
                f"Successfully triggered pipeline ({pipeline.id})",
                username=username
            )
        except ServerError as e:
            return ServerErrorResp(message=e)

        # Build the pipeline dispatch request
        pipeline_dispatch_request = request_builder.build(
            group,
            pipeline,
            event,
            commit=body.commit
        )

        # Dispatch the request
        pipeline_dispatcher.dispatch(pipeline_dispatch_request)

        # Respond with the event
        return ModelResponse(event)

    def _create_event(self, body, group, pipeline, message, username=None):
        # Persist the event in the database
        try:
            event = Event.objects.create(
                branch=body.branch,
                commit=body.commit,
                commit_sha=body.commit_sha,
                context_url=body.context_url,
                message=message,
                group=group,
                pipeline=pipeline,
                source=body.source,
                username=username
            )
        except (IntegrityError, DatabaseError, OperationalError) as e:
            raise ServerError(e.__cause__)

        return event