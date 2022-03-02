import json
from uuid import UUID

from backend.services.MessageBroker import message_service as broker
from backend.models import Pipeline


class PipelineService:
    def __init__(self):
        self.error = None

    def start(self, service_request):
        broker.publish("pipelines", json.dumps(service_request, default=self._uuid_convert))

    def _uuid_convert(self, obj):
        if isinstance(obj, UUID):
            return obj.hex # TODO change from hex to string

pipeline_service = PipelineService()

