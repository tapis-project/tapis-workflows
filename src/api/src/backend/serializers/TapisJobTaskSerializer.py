from backend.serializers import BaseTaskSerializer


class TapisJobTaskSerializer:
    @staticmethod
    def serialize(model, base=None):
        task = base if base != None else BaseTaskSerializer.serialize(model)

        task["tapis_job_def"] = model.tapis_job_def
        task["poll"] = model.poll

        return task