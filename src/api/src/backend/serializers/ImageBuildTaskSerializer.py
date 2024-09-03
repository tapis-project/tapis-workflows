from backend.serializers import BaseTaskSerializer
from backend.serializers.ContextSerializer import ContextSerializer
from backend.serializers.DestinationSerializer import DestinationSerializer
from pprint import pprint


class ImageBuildTaskSerializer:
    @staticmethod
    def serialize(model, base=None):
        task = base if base != None else BaseTaskSerializer.serialize(model)

        task["builder"] = model.builder
        task["context"] = ContextSerializer.serialize(model.context)
        task["destination"] = DestinationSerializer.serialize(model.destination)

        print("after dest serializer: ")
        pprint(task.destination)
        print("task")
        pprint(task)
        
        return task