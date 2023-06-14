from pprint import pprint
from uuid import uuid4
from django.forms import model_to_dict

from backend.utils.parse_directives import parse_directives as parse
from backend.conf.constants import WORKFLOW_EXECUTOR_ACCESS_TOKEN


class PipelineDispatchRequestBuilder:
    def __init__(self, secret_service):
        self.secret_service = secret_service

    def build(
        self,
        base_url,
        group,
        pipeline,
        event,
        commit=None,
        directives=None,
        params={}
    ):
        print("BASEURL in PipelineDispatchRequestBuilder", base_url)
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
        request["pipeline"] = model_to_dict(pipeline)
        # TODO Implement model and request object.
        request["pipeline"]["tasks"] = tasks_request
        request["pipeline"]["archives"] = archives

        # Populate the env for this request. Populate values from SK
        request["env"] = request["pipeline"]["env"]

        req_params = {}
        for key in params:
            req_params[key] = params[key].value

        # Populate the params for this request
        request["params"] = {
            "workflow_executor_access_token": {
                "value": WORKFLOW_EXECUTOR_ACCESS_TOKEN
            },
            "tapis_tenant_id": {
                "value": request["group"]["tenant_id"]
            },
            "tapis_pipeline_owner": {
                "value": request["pipeline"]["owner"]
            },
            **req_params
        }

        request["meta"] = {}
        # Properties to help uniquely identity a pipeline submission. If the workflow
        # executor is currently running a pipeline with the same values as the
        # properties provided in "idempotency_key", the workflow executor
        # will then take the appropriate action dictated by the
        # pipeline.duplicate_submission_policy (allow, allow_terminate, deny)
        request["meta"]["idempotency_key"] = [
            "group.id",
            "params.tapis_tenant_id",
            "pipeline.id"
        ]

        print("BASEURL before adding to request", base_url)
        request["meta"]["origin"] = base_url, # Origin of the request
        print("BASEURL in meta origin", request["meta"]["origin"])
        request["meta"]["event"] = model_to_dict(event)

        request["pipeline_run"] = {}
        
        # Generate the uuid for this pipeline run
        uuid = uuid4()
        request["pipeline_run"]["uuid"] = uuid

        # Parse the directives from the commit message
        directives_request = {}
        if commit != None:
            directives_request = parse(commit)

        if directives != None and len(directives) > 0:
            directive_str = f"[{'|'.join([d for d in directives])}]"
            directives_request = parse(directive_str)

        request["directives"] = directives_request

        print("FULL REQUEST")
        pprint(request)

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

    def _tapis_job(self, task):
        task_request = model_to_dict(task)
        return task_request

    def _tapis_actor(self, task):
        task_request = model_to_dict(task)
        return task_request

    def _function(self, task):
        task_request = model_to_dict(task)
        return task_request

    def _container_run(self, task):
        task_request = model_to_dict(task)
        return task_request