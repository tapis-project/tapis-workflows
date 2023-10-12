import json, logging

from uuid import UUID

from django.db import IntegrityError, DatabaseError, OperationalError
from django.utils import timezone

from backend.services.MessageBroker import service as broker
from backend.models import Pipeline, PipelineRun, RUN_STATUS_PENDING
from backend.errors.api import ServerError


class PipelineDispatcher:
    def __init__(self):
        self.error = None

    def dispatch(self, service_request: dict, pipeline):

        now = timezone.now()
        try: 
            # Create the pipeline run object
            pipeline_run = PipelineRun.objects.create(
                pipeline=pipeline,
                status=RUN_STATUS_PENDING,
                uuid=service_request["pipeline_run"]["uuid"],
                started_at=now,
                last_modified=now
            )

            # Update the pipeline object with the pipeline run
            pipeline = Pipeline.objects.filter(pk=pipeline.uuid).first()

            model_update = {"current_run": pipeline_run}
            service_request_update = {"current_run": pipeline_run.uuid}
            if pipeline.current_run != None:
                model_update["last_run"] = pipeline.current_run
                service_request_update = {"last_run": pipeline.current_run.uuid}

            Pipeline.objects.filter(pk=pipeline.uuid).update(**model_update)
            
            service_request["pipeline"].update(service_request_update)

        except (IntegrityError, DatabaseError, OperationalError) as e:
            message = f"Failed to create PipelineRun: {e.__cause__}"
            logging.error(message)
            raise ServerError(message=message)
        except Exception as e:
            logging.error(str(e))
            raise ServerError(message=str(e))

        try:
            broker.publish(
                "workflows",
                json.dumps(service_request, default=self._uuid_convert)
            )
        except Exception as e: # TODO use exact exception
            message = f"Failed publish the service request to the message broker: {e.__cause__}"
            logging.error(message)
            raise ServerError(message=message)
        
        return pipeline_run

    def _uuid_convert(self, obj):
        if isinstance(obj, UUID):
            return str(obj)

service = PipelineDispatcher()

