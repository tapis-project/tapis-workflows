import json

class DictFromTaskModel:
    @staticmethod
    def convert(model):
        entity = json.loads(model.json())
        entity = {
            **entity,
            **entity["execution_profile"]
        }
        del entity["execution_profile"]
        if entity.get("tags"):
            del entity["tags"]

        return entity