from backend.serializers import BaseTaskSerializer


class TemplateTaskSerializer:
    @staticmethod
    def serialize(model, base=None):
        # Returning only the base task because the only property relavent to
        # the template task (the `uses` property) is handled there.
        task = base if base != None else BaseTaskSerializer.serialize(model)

        return task