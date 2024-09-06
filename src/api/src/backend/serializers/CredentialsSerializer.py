from backend.serializers.UUIDSerializer import UUIDSerializer


class CredentialsSerializer:
    @staticmethod
    def serialize(model):
        if model == None:
            return None
        
        credential = {}
        credential["sk_id"] = model.sk_id
        credential["owner"] = model.owner
        credential["created_at"] = model.created_at
        credential["uuid"] = UUIDSerializer.serialize(model.uuid)

        
        return credential