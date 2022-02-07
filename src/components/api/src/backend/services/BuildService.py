import json

from backend.services.MessageBroker import message_service as broker


class BuildService:
    def start(self, pipeline_context):
        broker.publish("pipelines", json.dumps(pipeline_context))

        return # TODO return build object here

build_service = BuildService()

