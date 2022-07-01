from django.db import IntegrityError
from django.forms import model_to_dict

from backend.views.APIView import APIView
from backend.views.http.requests import WebhookEvent
from backend.views.http.responses.models import ModelResponse
from backend.views.http.responses.errors import ServerError
from backend.utils.parse_directives import parse_directives as parse
from backend.services.CredentialsService import CredentialsService
from backend.services import pipeline_dispatcher
from backend.models import Identity, Event, Pipeline, Group, GroupUser


WEBHOOK_SOURCE_GITHUB = "github"
WEBHOOK_SOURCE_GITLAB = "gitlab"
WEBHOOK_SOURCES = [WEBHOOK_SOURCE_GITHUB, WEBHOOK_SOURCE_GITLAB]

cred_service = CredentialsService()

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
                )
            )

        # If an identity is found with the username provided in the 
        # webhook notification, this pipeline can be dispatched
        username = None
        for identity in identities:
            # Fetch the credentials
            identity_username = getattr(
                cred_service.get_secret(identity.sk_id),
                "username",
                False
            )

            if identity_username and identity_username == body.username:
                username = identity_username
                break


        if username == None:
            event = self._create_event(
                body,
                group,
                pipeline,
                f"Pipeline failed to run. No identity found type '{body.source}' and username '{body.username}'"
            )
            return ModelResponse(event)

        
        # Create the event
        event = self._create_event(
            body,
            group,
            pipeline,
            f"Successfully triggered pipeline ({pipeline.id})",
            username=username
        )
   
        # Get the pipeline actions, their contexts, destinations, and respective
        # credentials and generate a piplines_service_request
        actions = pipeline.actions.all()
        
        actions_request = []
        for action in actions:
            # Build action result
            action_request = getattr(self, f"_{action.type}")(action)
            actions_request.append(action_request)

        # Get the archives for this pipeline
        archives = []
        pipeline_archives = pipeline.archives.all()
        for pipeline_archive in pipeline_archives:
            # Fetch any credentials or identities for required to
            # access this archive
            # TODO Handle creds/identity for archives
            archives.append(model_to_dict(pipeline_archive.archive))

        # Convert pipleline to a dict and build the pipeline_dispatch_request
        pipeline_dispatch_request = {}
        pipeline_dispatch_request["group"] = model_to_dict(group)
        pipeline_dispatch_request["event"] = model_to_dict(event)
        pipeline_dispatch_request["pipeline"] = model_to_dict(pipeline)
        pipeline_dispatch_request["pipeline"]["actions"] = actions_request
        pipeline_dispatch_request["pipeline"]["archives"] = archives

        # Parse the directives from the commit message
        directives = parse(body.commit)
        pipeline_dispatch_request["directives"] = directives

        # Dispatch the request
        pipeline_dispatcher.dispatch(pipeline_dispatch_request)

        # Respond with the event
        return ModelResponse(event)

    def _image_build(self, action):
        action_request = model_to_dict(action)

        action_request["context"] = model_to_dict(action.context)

        # Resolve which context credentials to use if any provided
        context_creds = None
        if action.context.credentials != None:
            context_creds = action.context.credentials
        
        # Identity takes precedence over credentials placed directly in
        # the context
        if action.context.identity != None:
            context_creds = action.context.identity.credentials

        action_request["context"]["credentials"] = None
        if context_creds != None:
            action_request["context"]["credentials"] = model_to_dict(context_creds)

            # Get the context credentials data
            context_cred_data = cred_service.get_secret(context_creds.sk_id)
            action_request["context"]["credentials"]["data"] = context_cred_data

        # Destination credentials
        action_request["destination"] = model_to_dict(action.destination)

        destination_creds = None
        if action.destination.credentials != None:
            destination_creds = action.destination.credentials

        if action.destination.identity != None:
            destination_creds = action.destination.identity.credentials

        if destination_creds != None:
            action_request["destination"]["credentials"] = model_to_dict(destination_creds)

            # Get the context credentials data
            destination_cred_data = cred_service.get_secret(destination_creds.sk_id)
            action_request["destination"]["credentials"]["data"] = destination_cred_data

        return action_request

    def _webhook_notification(self, action):
        action_request = model_to_dict(action)
        return action_request

    def _container_run(self, action):
        action_request = model_to_dict(action)
        return action_request

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
        except IntegrityError as e:
            return ServerError(message=e.__cause__)

        return event