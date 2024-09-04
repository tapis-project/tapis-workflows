from uuid import uuid4
from django.forms import model_to_dict

from backend.utils.parse_directives import parse_directives as parse
from backend.conf.constants import WORKFLOW_EXECUTOR_ACCESS_TOKEN
from backend.serializers import TaskSerializer, PipelineSerializer


class PipelineDispatchRequestBuilder:
    def __init__(self, secret_service):
        self.secret_service = secret_service

    def build(
        self,
        base_url,
        group,
        pipeline,
        name=None,
        description=None,
        commit=None,
        directives=None,
        args={}
    ):
        # Get the pipeline tasks, their contexts, destinations, and respective
        # credentials and generate a piplines_service_request
        tasks = pipeline.tasks.all()
        
        # Convert tasks' schema to the schema expected by the workflow engine
        tasks_request = []
        for task in tasks:
            # Convert the task to a dict
            serialized_task = TaskSerializer.serialize(task)

            # Handle the task-specific schema conversions
            task_request = getattr(self, f"_{task.type}")(serialized_task, task)
            tasks_request.append(task_request)


        # Serialize the pipeline and it's tasks
        request = {}
        request["pipeline"] = PipelineSerializer.serialize(pipeline)
        request["pipeline"]["tasks"] = tasks_request

        # Populate the env for this request.
        request["env"] = request["pipeline"]["env"]
        
        # Serialize the archives
        request["archives"] = []
        pipeline_archives = pipeline.archives.all()
        for pipeline_archive in pipeline_archives:
            # Fetch any credentials or identities for required to
            # access this archive
            # TODO Handle creds/identity for archives
            request["archives"].append(model_to_dict(pipeline_archive.archive))
        
        req_args = {}
        for key in args:
            req_args[key] = args[key].dict()
            
        # Populate the args for this request
        request["args"] = {
            "workflow_executor_access_token": {
                "value": WORKFLOW_EXECUTOR_ACCESS_TOKEN
            },
            "tapis_tenant_id": {
                "value": request["group"]["tenant_id"]
            },
            "tapis_pipeline_owner": {
                "value": request["pipeline"]["owner"]
            },
            **req_args
        }

        request["meta"] = {}

        # Add the group to the meta so it can be used to determine the idemp key
        request["meta"]["group"] = model_to_dict(group)

        # Properties to help uniquely identity a pipeline submission. If the workflow
        # executor is currently running a pipeline with the same values as the
        # properties provided in "idempotency_key", the workflow executor
        # will then take the appropriate action dictated by the
        # pipeline.duplicate_submission_policy (allow, allow_terminate, deny)
        request["meta"]["idempotency_key"] = [
            "meta.group.id",
            "args.tapis_tenant_id",
            "pipeline.id"
        ]

        request["meta"]["origin"] = base_url # Origin of the request

        request["pipeline_run"] = {}
        
        # Generate the uuid for this pipeline run
        uuid = uuid4()
        request["pipeline_run"]["uuid"] = uuid
        request["pipeline_run"]["name"] = name or uuid
        request["pipeline_run"]["description"] = description

        # # Parse the directives from the commit message
        # directives_request = {}
        # if commit != None:
        #     directives_request = parse(commit)

        # if directives != None and len(directives) > 0:
        #     directive_str = f"[{'|'.join([d for d in directives])}]"
        #     directives_request = parse(directive_str)

        # request["directives"] = directives_request

        request["directives"] = {}

        return request

    def _image_build(self, task_request, task):
        context_creds = None
        if task.context.credentials != None:
            context_creds = task.context.credentials

        if context_creds != None:
            # Get the context credentials data
            context_cred_data = self.secret_service.get_secret(context_creds.sk_id)
            task_request["context"]["credentials"] = context_cred_data

        # NOTE Workflow engine expect build_file_path and not recipe_file_path
        # TODO REMOVE FIXME Migrate "recipe_file_path" to "build_file_path"
        task_request["context"]["build_file_path"] = task_request["context"]["recipe_file_path"]
        del task_request["context"]["recipe_file_path"]

        # Destination credentials
        destination_creds = None
        if task.destination.credentials != None:
            destination_creds = task.destination.credentials

        if destination_creds != None:
            # Get the context credentials data
            destination_cred_data = self.secret_service.get_secret(destination_creds.sk_id)
            task_request["destination"]["credentials"] = destination_cred_data

        return task_request

    def _request(self, task_request, _):
        return task_request

    def _application(self, task_request, _):
        return task_request
    
    def _template(self, task_request, _):
        return task_request

    def _tapis_job(self, task_request, _):
        return task_request

    def _tapis_actor(self, task_request, _):
        return task_request

    def _function(self, task_request, _):
        return task_request

    def _container_run(self, task_request, _):
        return task_request