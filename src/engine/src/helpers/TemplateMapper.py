from typing import Union

from .TemplateRepository import TemplateRepository
from ..owe_python_sdk.schema import (
    Uses,
    Pipeline,
    Task,
    TemplateTask,
    FunctionTask,
    ApplicationTask,
    ImageBuildTask,
    RequestTask,
    TapisJobTask,
    TapisActorTask
)

class TemplateMapper:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        self.task_map_by_type = {
            "function": FunctionTask,
            "application": ApplicationTask,
            "image_build": ImageBuildTask,
            "request": RequestTask,
            "tapis_job": TapisJobTask,
            "tapis_actor": TapisActorTask
        }

    def map(self, obj: Union[Pipeline, Task], uses: Uses):
        # Clone git repository specified on the pipeline.uses if exists
        template = TemplateRepository(uses, cache_dir=self.cache_dir)

        for attr in template.keys():
            # For pipelines only. Skip the tasks property as they should be handled
            # seperately in another call to the map method of the Template ampper
            if attr == "tasks":
                continue

            # For task only. The template should specify the correct type. For all other properties,
            # that are not specified, we use that which in enumerated in the template
            if attr == "type":
                obj.type = template.get(attr)
                continue

            if getattr(obj, attr) == None:
                setattr(obj, attr, template[attr])

        return obj