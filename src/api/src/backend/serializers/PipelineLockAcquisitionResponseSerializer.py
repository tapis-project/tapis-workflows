from backend.serializers import UUIDSerializer
from backend.conf.constants import DATETIME_FORMAT


class PipelineLockAcquisitionResponseSerializer:
    @staticmethod
    def serialize(pipeline_lock, message):
        return {
            "acquired": pipeline_lock.acquired,
            "message": message,
            "pipeline_lock_uuid": UUIDSerializer.serialize(pipeline_lock.uuid)
        }