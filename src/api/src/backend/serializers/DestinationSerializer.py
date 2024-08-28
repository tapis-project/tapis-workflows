from backend.serializers.CredentialsSerializer import CredentialsSerializer
from backend.serializers.UUIDSerializer import UUIDSerializer


class DestinationSerializer:
    @staticmethod
    def serialize(model):
        destination = {}
        destination["tag"] = model.tag,
        destination["type"] = model.type,
        destination["url"] = model.url,
        destination["filename"] = model.filename,
        destination["credentials"] = CredentialsSerializer.serialize(model.credentials)
        destination["uuid"] = UUIDSerializer.serialize(model.uuid)
        
        return destination