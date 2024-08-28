from backend.serializers import BaseTaskSerializer


class ApplicationTaskSerializer:
    @staticmethod
    def serialize(model, base=None):
        task = base if base != None else BaseTaskSerializer.serialize(model)

        task["image"] = model.image

        return task