import json, logging

from uuid import UUID, uuid4

from django.db import IntegrityError, DatabaseError, OperationalError

from backend.services.MessageBroker import service as broker
from backend.models import Pipeline, PipelineRun, RUN_STATUS_PENDING
from backend.errors.api import ServerError
from backend.conf.constants import WORKFLOW_EXECUTOR_ACCESS_TOKEN


class PipelineDispatcher:
    def __init__(self):
        self.error = None

    def dispatch(self, service_request: dict, pipeline):
        # Tell the workflow executors which backends and archivers to use.
        # Add the workflow executor access token to the request. This enables
        # the workflow executor to make calls to special endpoints on the API.
        service_request["middleware"] = {
            "backends": {
                "tapisworkflowsapi": {
                    "access_token": WORKFLOW_EXECUTOR_ACCESS_TOKEN
                }
            },
            "archivers": {
                "tapissystem": {}
            }
        }

        service_request["meta"] = {}
        # Properties to help uniquely identity a pipeline submission. If the workflow
        # executor is currently running a pipeline with the same values as the
        # properties provided in "unique_constraint", the workflow executor
        # will then take the appropriate action dictated by the
        # pipeline.duplicate_submission_policy (allow, allow_terminate, deny)
        service_request["meta"]["unique_constraints"] = [
            "group.id",
            "group.tenant_id",
            "pipeline.id"
        ]

        service_request["pipeline_run"] = {}
        
        # Generate the uuid for this pipeline run
        uuid = uuid4()
        service_request["pipeline_run"]["uuid"] = uuid

        try: 
            # Create the pipeline run object
            pipeline_run = PipelineRun.objects.create(
                pipeline=pipeline,
                status=RUN_STATUS_PENDING,
                uuid=uuid,
            )

            # Update the pipeline object with the pipeline run
            Pipeline.objects.filter(
                pk=pipeline.uuid).update(current_run=pipeline_run)

        except (IntegrityError, DatabaseError, OperationalError) as e:
            message = f"Failed to create PipelineRun: {e.__cause__}"
            logging.error(message)
            raise ServerError(message=message)

        try:
            broker.publish(
                "workflows",
                json.dumps(service_request, default=self._uuid_convert)
            )
        except Exception as e: # TODO use exact exception
            message = f"Failed publish the service request to the message broker: {e.__cause__}"
            logging.error(message)
            raise ServerError(message=message)

    def _uuid_convert(self, obj):
        if isinstance(obj, UUID):
            return str(obj)

service = PipelineDispatcher()

