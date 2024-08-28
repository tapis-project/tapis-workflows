from backend.serializers import BaseTaskSerializer


class TapisActorTaskSerializer:
    @staticmethod
    def serialize(model, base=None):
        task = base if base != None else BaseTaskSerializer.serialize(model)

        task["tapis_actor_id"] = model.tapis_job_def
        task["poll"] = model.poll
        task["tapis_actor_message"] = model.tapis_actor_message

        return task