from django.forms.models import model_to_dict

from backend.serializers import UUIDSerializer
from backend.conf.constants import DATETIME_FORMAT


class PipelineLockModelSerializer:
    @staticmethod
    def serialize(model):
        lock = model_to_dict(model)
        from pprint import pprint
        pprint(lock)
        lock["uuid"] = UUIDSerializer.serialize(lock["uuid"])
        lock["created_at"] = lock["created_at"].strftime(DATETIME_FORMAT)

        if lock["acquired_at"] != None:
            lock["acquired_at"] = lock["acquired_at"].strftime(DATETIME_FORMAT)

        lock["pipeline_id"] = model.pipeline.id
        del lock["pipeline"]

        lock["pipeline_run_uuid"] = UUIDSerializer.serialize(model.pipeline_run.uuid)
        del lock["pipeline_run"]

        return lock