import json

from backend.services.MessageBroker import message_service as broker
from backend.models import Pipeline


class PipelineService:
    def __init__(self):
        self.error = None

    def start(self, service_request):
        broker.publish("pipelines", json.dumps(service_request))

        return # TODO return build object here

pipeline_service = PipelineService()

