from backend.serializers.UUIDSerializer import UUIDSerializer
from backend.serializers.SecretSerializer import SecretSerializer


class GroupSecretSerializer:
    @staticmethod
    def serialize(model):
        group_secret = {}
        group_secret["id"] = model.id
        group_secret["group_id"] = model.group.id
        group_secret["secret"] = SecretSerializer.serialize(model.secret)
        group_secret["uuid"] = UUIDSerializer.serialize(model.uuid)
        
        return group_secret