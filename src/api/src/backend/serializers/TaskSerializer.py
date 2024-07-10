from backend.serializers import FunctionTaskSerializer

class TaskSerializer:
    @staticmethod
    def serialize(model):
        if model.type == "function":
            return FunctionTaskSerializer.serialize(model)