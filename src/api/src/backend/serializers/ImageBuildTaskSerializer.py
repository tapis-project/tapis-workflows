from backend.serializers import BaseTaskSerializer
from backend.serializers.ContextSerializer import ContextSerializer
from backend.serializers.DestinationSerializer import DestinationSerializer


class ImageBuildTaskSerializer:
    @staticmethod
    def serialize(model, base=None):
        task = base if base != None else BaseTaskSerializer.serialize(model)

        task["builder"] = model.builder
        task["context"] = ContextSerializer.serialize(model.context)
        task["destination"] = DestinationSerializer(model.destination)
        
        return task