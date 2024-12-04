import json

class TaskDTOSerializer:
    @staticmethod
    def serialize(model):
        entity = json.loads(model.json())
        entity = {
            **entity,
            **entity["execution_profile"]
        }
        del entity["execution_profile"]

        return entity