import json

class DictFromPydanticTaskModel:
    @staticmethod
    def convert(model):
        entity = json.loads(model.json())
        if entity.get("tags", None) != None:
            del entity["tags"]
            
        entity = {
            **entity,
            **entity["execution_profile"]
        }
        del entity["execution_profile"]

        return entity