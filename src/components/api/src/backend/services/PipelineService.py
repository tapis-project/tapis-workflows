import json

from backend.services.MessageBroker import message_service as broker
from backend.services.ContextService import context_service
from backend.services.DestinationService import destination_service
from backend.models import Pipeline


class PipelineService:
    def __init__(self):
        self.error = None

    def start(self, pipeline_context):
        broker.publish("pipelines", json.dumps(pipeline_context))

        return # TODO return build object here

    def validate(self, pipeline_request):
        # Set the error if context could not be validated
        if not context_service.validate(pipeline_request["context"]):
            self.error = f"Context error for Pipeline: {context_service.error}"
            return False

        # Set the error if destination could not be validated
        if not destination_service.validate(pipeline_request["destination"]):
            self.error = f"Destination error for Pipeline: {context_service.error}"
            return False

    def build(self, pipeline_request):
        # Persist the event in the database
        return Pipeline.objects.create(**pipeline_request)

pipeline_service = PipelineService()

