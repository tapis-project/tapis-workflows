from backend.serializers import BaseTaskSerializer
from backend.serializers.CredentialsSerializer import CredentialsSerializer


class RequestTaskSerializer:
    @staticmethod
    def serialize(model, base=None):
        task = base if base != None else BaseTaskSerializer.serialize(model)

        task["auth"] = CredentialsSerializer.serialize(model.auth)
        task["data"] = model.data
        task["headers"] = model.headers
        task["http_method"] = model.http_method
        task["protocol"] = model.protocol
        task["query_params"] = model.query_params
        task["url"] = model.url

        return task