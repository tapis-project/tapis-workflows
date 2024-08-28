from backend.serializers.CredentialsSerializer import CredentialsSerializer
from backend.serializers.UUIDSerializer import UUIDSerializer


class ContextSerializer:
    @staticmethod
    def serialize(model):
        context = {}
        context["branch"] = model
        context["credentials"] = CredentialsSerializer.serialize(model.credentials)
        context["recipe_file_path"] = model.recipe_file_path
        context["sub_path"] = model.sub_path
        context["tag"] = model.tag
        context["type"] = model.type
        context["url"] = model.url
        context["visibility"] = model.visibility
        context["uuid"] = UUIDSerializer.serialize(model.uuid)
        
        return context