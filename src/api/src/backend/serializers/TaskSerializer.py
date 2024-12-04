from backend.serializers.BaseTaskSerializer import BaseTaskSerializer
from backend.serializers.FunctionTaskSerializer import FunctionTaskSerializer
from backend.serializers.ImageBuildTaskSerializer import ImageBuildTaskSerializer
from backend.serializers.TapisActorTaskSerializer import TapisActorTaskSerializer
from backend.serializers.TapisJobTaskSerializer import TapisJobTaskSerializer
from backend.serializers.ApplicationTaskSerializer import ApplicationTaskSerializer
from backend.serializers.TemplateTaskSerializer import TemplateTaskSerializer
from backend.serializers.RequestTaskSerializer import RequestTaskSerializer
from backend.models import (
    TASK_TYPE_FUNCTION,
    TASK_TYPE_APPLICATION,
    TASK_TYPE_TEMPLATE,
    TASK_TYPE_TAPIS_ACTOR,
    TASK_TYPE_IMAGE_BUILD,
    TASK_TYPE_REQUEST,
    TASK_TYPE_TAPIS_JOB
)

class TaskSerializer:
    @staticmethod
    def serialize(model):
        base = BaseTaskSerializer.serialize(model)

        if model.type == TASK_TYPE_FUNCTION:
            return FunctionTaskSerializer.serialize(model, base=base)
        
        if model.type == TASK_TYPE_TEMPLATE:
            return TemplateTaskSerializer.serialize(model, base=base)
        
        if model.type == TASK_TYPE_IMAGE_BUILD:
            return ImageBuildTaskSerializer.serialize(model, base=base)
        
        if model.type == TASK_TYPE_TAPIS_JOB:
            return TapisJobTaskSerializer.serialize(model, base=base)
        
        if model.type == TASK_TYPE_TAPIS_ACTOR:
            return TapisActorTaskSerializer.serialize(model, base=base)
        
        if model.type == TASK_TYPE_REQUEST:
            return RequestTaskSerializer.serialize(model, base=base)

        if model.type == TASK_TYPE_APPLICATION:
            return ApplicationTaskSerializer.serialize(model, base=base)
        
        raise NotImplementedError(f"Task Serializer does not have a method for serializing tasks of type '{model.type}'")