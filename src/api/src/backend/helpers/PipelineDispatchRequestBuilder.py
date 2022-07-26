from django.forms import model_to_dict

from backend.utils.parse_directives import parse_directives as parse


class PipelineDispatchRequestBuilder:
    def __init__(self, secret_service):
        self.secret_service = secret_service

    def build(self, group, pipeline, event, commit=None, directives=None):
        # Get the pipeline tasks, their contexts, destinations, and respective
        # credentials and generate a piplines_service_request
        tasks = pipeline.tasks.all()
        
        tasks_request = []
        for task in tasks:
            # Build task result
            task_request = getattr(self, f"_{task.type}")(task)
            tasks_request.append(task_request)

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
        request["pipeline"]["tasks"] = tasks_request
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

    def _image_build(self, task):
        task_request = model_to_dict(task)

        task_request["context"] = model_to_dict(task.context)

        # Resolve which context credentials to use if any provided
        context_creds = None
        if task.context.credentials != None:
            context_creds = task.context.credentials
        
        # Identity takes precedence over credentials placed directly in
        # the context
        if task.context.identity != None:
            context_creds = task.context.identity.credentials

        task_request["context"]["credentials"] = None
        if context_creds != None:
            task_request["context"]["credentials"] = model_to_dict(context_creds)

            # Get the context credentials data
            context_cred_data = self.secret_service.get_secret(context_creds.sk_id)
            task_request["context"]["credentials"]["data"] = context_cred_data

        # Destination credentials
        task_request["destination"] = model_to_dict(task.destination)

        destination_creds = None
        if task.destination.credentials != None:
            destination_creds = task.destination.credentials

        if task.destination.identity != None:
            destination_creds = task.destination.identity.credentials

        if destination_creds != None:
            task_request["destination"]["credentials"] = model_to_dict(destination_creds)

            # Get the context credentials data
            destination_cred_data = self.secret_service.get_secret(destination_creds.sk_id)
            task_request["destination"]["credentials"]["data"] = destination_cred_data

        return task_request

    def _request(self, task):
        task_request = model_to_dict(task)
        return task_request

    def _container_run(self, task):
        task_request = model_to_dict(task)
        return task_request