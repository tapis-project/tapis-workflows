from backend.serializers.UUIDSerializer import UUIDSerializer


class SecretSerializer:
    @staticmethod
    def serialize(model):
        secret = {}
        secret["id"] = model.id
        secret["description"] = model.description
        secret["tenant_id"] = model.tenant_id
        secret["owner"] = model.owner
        secret["sk_secret_name"] = model.sk_secret_name
        secret["uuid"] = UUIDSerializer.serialize(model.uuid)
        
        return secret