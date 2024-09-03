from backend.serializers.CredentialsSerializer import CredentialsSerializer
from backend.serializers.UUIDSerializer import UUIDSerializer


class DestinationSerializer:
    @staticmethod
    def serialize(model):
        if model == None:
            return None
        destination = {}
        destination["tag"] = model.tag,
        destination["type"] = model.type,
        destination["url"] = model.url,
        destination["filename"] = model.filename,
        destination["credentials"] = CredentialsSerializer.serialize(model.credentials)
        destination["uuid"] = UUIDSerializer.serialize(model.uuid)

        print("tag", model.tag, type(model.tag))
        print("type", model.type, type(model.type))
        print("url", model.url, type(model.url))
        print("filename", model.filename, type(model.filename))
        
        return destination