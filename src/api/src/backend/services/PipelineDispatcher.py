import json

from uuid import UUID

from django.db import IntegrityError, DatabaseError, OperationalError
from django.utils import timezone
from backend.utils import logger
from backend.services.MessageBroker import service as broker
from backend.models import Pipeline, PipelineRun, RUN_STATUS_SUBMITTED
from backend.errors.api import ServerError


class PipelineDispatcher:
    def __init__(self):
        self.error = None

    def dispatch(self, service_request: dict, pipeline, pipeline_run=None):

        now = timezone.now()
        try: 
            # Create the pipeline run object if one was not provied
            if pipeline_run == None:
                pipeline_run = PipelineRun.objects.create(
                    name=service_request["pipeline_run"]["name"],
                    description=service_request["pipeline_run"]["description"],
                    pipeline=pipeline,
                    status=RUN_STATUS_SUBMITTED,
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
            logger.exception(e.__cause__)
            raise ServerError(message=message)
        except Exception as e:
            logger.exception(e.__cause__)
            raise ServerError(message=str(e))

        try:
            broker.publish(
                "workflows",
                json.dumps(service_request, default=self._uuid_convert)
            )
        except Exception as e: # TODO use exact exception
            message = f"Failed publish the service request to the message broker: {e.__cause__}"
            logger.error(message)
            logger.exception(e.__cause__)
            raise ServerError(message=message)
        
        return pipeline_run

    def _uuid_convert(self, obj):
        if isinstance(obj, UUID):
            return str(obj)

service = PipelineDispatcher()

