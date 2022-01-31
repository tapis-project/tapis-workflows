import json

from backend.services.MessageBroker import message_service as broker


class BuildService:
    def start(self, build_context):
        broker.publish("builds", json.dumps(build_context))

        return # TODO return build object here

build_service = BuildService()

