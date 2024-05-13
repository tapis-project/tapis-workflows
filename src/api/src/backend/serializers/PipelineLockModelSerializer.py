from django.forms.models import model_to_dict

from backend.serializers import UUIDSerializer
from backend.conf.constants import DATETIME_FORMAT


class PipelineLockModelSerializer:
    @staticmethod
    def serialize(model, pipeline):
        lock = {}
        lock["uuid"] = UUIDSerializer.serialize(lock.uuid)
        lock["created_at"] = lock.created_at.strftime(DATETIME_FORMAT)
        lock["expires_in"] = lock.expires_in

        if lock.acquired_at != None:
            lock["acquired_at"] = lock.acquired_at.strftime(DATETIME_FORMAT)

        lock["pipeline_id"] = pipeline.id
        lock["pipeline_run_uuid"] = UUIDSerializer.serialize(model.pipeline_run_id)

        return lock