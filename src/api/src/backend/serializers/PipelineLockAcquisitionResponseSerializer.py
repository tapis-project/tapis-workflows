from backend.serializers import UUIDSerializer


class PipelineLockAcquisitionResponseSerializer:
    @staticmethod
    def serialize(pipeline_lock, message):
        return {
            "acquired": pipeline_lock.acquired_at != None,
            "message": message,
            "pipeline_lock_uuid": UUIDSerializer.serialize(pipeline_lock.uuid)
        }