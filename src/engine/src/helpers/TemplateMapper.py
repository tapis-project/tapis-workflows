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

    def map(self, obj: Union[Pipeline, Task], uses: Uses) -> Union[Pipeline, Task]:
        """This method takes an object(Pipeline or Task object), and updates its
        attributes with the values found in the templates
        
        IMPORTANT NOTE:
        The original object is modified and returned by this function, not a copy.
        """

        # Clone git repository specified on the pipeline.uses if exists
        template = TemplateRepository(uses, cache_dir=self.cache_dir)

        # Resolve which class the final object should have
        obj_class = Pipeline
        if not issubclass(obj.__class__, Pipeline):
            obj_class = self.task_map_by_type.get(obj.get("type"), None)

        # Raise exception if no class could be resolved from the template
        if obj_class == None:
            raise Exception(f"Invalid Template: Unable to resolve object type from Template. Task template object 'type' property must be one of [{self.task_map_by_type.keys()}]")

        dict_obj = obj.dict()

        for attr in template.keys():
            # For pipelines only. Skip the tasks property as they should be handled
            # seperately in another call to the map method of the Template ampper
            if attr == "tasks":
                continue

            # For task only. The template should specify the correct type. For all other properties,
            # that are not specified, we use that which in enumerated in the template
            if attr == "type":
                dict_obj["type"] = template.get(attr)
                continue

            if obj.get(attr, None) == None:
                dict_obj[attr] = template[attr]

        new_obj = obj_class(**dict_obj)

        for attr in vars(new_obj):
            if attr == "tasks":
                continue

            updated_value = getattr(new_obj, attr)
            original_value = getattr(obj, attr)
            if original_value != updated_value:
                setattr(obj, attr, updated_value)

        return obj