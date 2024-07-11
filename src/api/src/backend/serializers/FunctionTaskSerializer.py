from backend.serializers import BaseTaskSerializer

class FunctionTaskSerializer:
    @staticmethod
    def serialize(model, base=None):
        task = base if base != None else BaseTaskSerializer.serialize(model)

        task["git_repositories"] = model.git_repositories
        task["code"] = model.code
        task["runtime"] = model.runtime
        task["command"] = model.command
        task["installer"] = model.installer
        task["packages"] = model.packages
        task["entrypoint"] = model.entrypoint
        
        return task