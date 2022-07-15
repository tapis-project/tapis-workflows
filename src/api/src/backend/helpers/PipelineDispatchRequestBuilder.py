from django.forms import model_to_dict

from backend.utils.parse_directives import parse_directives as parse


class PipelineDispatchRequestBuilder:
    def __init__(self, cred_service):
        self.cred_service = cred_service

    def build(self, group, pipeline, event, commit=None, directives=None):
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

        # Convert pipleline to a dict and build the request
        request = {}
        request["group"] = model_to_dict(group)
        request["event"] = model_to_dict(event)
        request["pipeline"] = model_to_dict(pipeline)
        request["pipeline"]["actions"] = actions_request
        request["pipeline"]["archives"] = archives

        # Parse the directives from the commit message
        directives_request = {}
        if commit != None:
            directives_request = parse(commit)

        if directives != None and len(directives) > 0:
            directive_str = f"[{'|'.join([d for d in directives])}]"
            directives_request = parse(directive_str)

        request["directives"] = directives_request

        return request

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
            context_cred_data = self.cred_service.get_secret(context_creds.sk_id)
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
            destination_cred_data = self.cred_service.get_secret(destination_creds.sk_id)
            action_request["destination"]["credentials"]["data"] = destination_cred_data

        return action_request

    def _webhook_notification(self, action):
        action_request = model_to_dict(action)
        return action_request

    def _container_run(self, action):
        action_request = model_to_dict(action)
        return action_request