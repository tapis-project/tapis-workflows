import json

from backend.services.MessageBroker import message_service as broker
from backend.models import Pipeline


class PipelineService:
    def __init__(self):
        self.error = None

    def start(self, pipeline_context):
        broker.publish("pipelines", json.dumps(pipeline_context))

        return # TODO return build object here

pipeline_service = PipelineService()

