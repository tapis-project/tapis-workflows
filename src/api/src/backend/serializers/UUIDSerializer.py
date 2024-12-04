from uuid import UUID

class UUIDSerializer:
    @staticmethod
    def serialize(uuid):
        if isinstance(uuid, UUID):
            return str(uuid)
        
        return uuid