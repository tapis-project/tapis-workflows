import json
from uuid import UUID

from backend.services.MessageBroker import service as broker


class PipelineDispatcher:
    def __init__(self):
        self.error = None

    def dispatch(self, service_request):
        broker.publish("pipelines", json.dumps(service_request, default=self._uuid_convert))

    def _uuid_convert(self, obj):
        if isinstance(obj, UUID):
            return str(obj)

service = PipelineDispatcher()

