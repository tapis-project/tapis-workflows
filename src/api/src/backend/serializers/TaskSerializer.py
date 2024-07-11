from backend.serializers import (
    FunctionTaskSerializer,
    BaseTaskSerializer,
)
from backend.models import TASK_TYPE_FUNCTION

class TaskSerializer:
    @staticmethod
    def serialize(model):
        base = BaseTaskSerializer.serialize(model)

        if model.type == TASK_TYPE_FUNCTION:
            return FunctionTaskSerializer.serialize(model, base=base)
        
        raise NotImplementedError(f"Task Serializer does not have a method for serializing tasks of type '{model.type}'")