from uuid import uuid4
from django.forms import model_to_dict
from pprint import pprint

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
        # Get the pipeline tasks, their contexts, destinations, and respective
        # credentials and generate a piplines_service_request
        tasks = pipeline.tasks.all()
        
        # Convert tasks' schema to the schema expected by the workflow engine
        tasks_request = []
        for task in tasks:
            # Convert the task to a dict and add the execution profile property
            # for all tasks.
            preprocessed_task = self._preprocess_task(task)

            # Handle the task-specific schema conversions
            task_request = getattr(self, f"_{task.type}")(preprocessed_task, task)
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
        request["archives"] = archives

        # Move the execution profile props from the pipeline object to the
        # execution profile property
        request["pipeline"]["execution_profile"] = {
            "max_exec_time": request["pipeline"]["max_exec_time"],
            "duplicate_submission_policy": request["pipeline"]["duplicate_submission_policy"],
            "max_retries": request["pipeline"]["max_retries"],
            "invocation_mode": request["pipeline"]["invocation_mode"],
            "retry_policy": request["pipeline"]["retry_policy"]
        }

        request["pipeline"]["tasks"] = tasks_request

        # Populate the env for this request. Populate values from SK
        request["env"] = request["pipeline"]["env"]

        # req_params = {}
        # for key in params:
        #     req_params[key] = params[key].value

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
            **params
        }

        pprint(request)

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

        request["meta"]["origin"] = base_url # Origin of the request
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

        return request

    def _image_build(self, task_request, task):
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
            task_request["context"]["credentials"] = context_cred_data

        # NOTE Workflow engine expect build_file_path and not recipe_file_path
        # TODO REMOVE FIXME Migrate "recipe_file_path" to "build_file_path"
        task_request["context"]["build_file_path"] = task_request["context"]["recipe_file_path"]
        del task_request["context"]["recipe_file_path"]

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
            task_request["destination"]["credentials"] = destination_cred_data

        return task_request

    def _request(self, task_request, _):
        return task_request

    def _application(self, task_request, _):
        return task_request

    def _tapis_job(self, task_request, _):
        return task_request

    def _tapis_actor(self, task_request, _):
        return task_request

    def _function(self, task_request, _):
        return task_request

    def _container_run(self, task_request, _):
        return task_request

    def _preprocess_task(self, task):
        # Convert to dict
        task_request = model_to_dict(task)

        # Map task data model properties to the workflow engine expected schema for
        # the execution profile
        task_request["execution_profile"] = {
            "flavor": task_request["flavor"],
            "max_exec_time": task_request["max_exec_time"],
            "max_retries": task_request["max_retries"],
            "invocation_mode": task_request["invocation_mode"],
            "retry_policy": task_request["retry_policy"]
        }

        return task_request