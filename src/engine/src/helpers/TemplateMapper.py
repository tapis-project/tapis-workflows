from typing import Union

from .TemplateRepository import TemplateRepository
from owe_python_sdk.schema import (
    Uses,
    Pipeline,
    Task,
    FunctionTask,
    ApplicationTask,
    ImageBuildTask,
    RequestTask,
    TapisJobTask,
    TapisActorTask
)


class TemplateMapper:
    def __init__(self, cache_dir: str):
        self.task_map_by_type = {
            "function": FunctionTask,
            "application": ApplicationTask,
            "image_build": ImageBuildTask,
            "request": RequestTask,
            "tapis_job": TapisJobTask,
            "tapis_actor": TapisActorTask
        }
        self.template_repo = TemplateRepository(cache_dir=cache_dir)

    def map(self, obj: Union[Pipeline, Task], uses: Uses) -> Union[Pipeline, Task]:
        """This method takes an object(Pipeline or Task object), and updates its
        attributes with the values found in the templates
        
        IMPORTANT NOTE:
        The original object is modified and returned by this function, not a copy.
        """

        # Clone git repository specified on the pipeline.uses if exists
        template = self.template_repo.get_by_uses(uses)
        
        # Resolve which class the final object should have
        obj_class = Pipeline
        if not issubclass(obj.__class__, Pipeline):
            obj_class = self.task_map_by_type.get(template.get("type", None), None)

        # Raise exception if no class could be resolved from the template
        if obj_class == None:
            raise Exception(f"Invalid Template: Unable to resolve object type from Template. Task template object 'type' property must be one of {list(self.task_map_by_type.keys())} | Recieved: {template.get('type', 'None')}")

        dict_obj = obj.dict()

        # Create a dictionary of the original object and map the properties of the template
        # onto the dictionary
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
            
            # Add the template's value for this attribute if the original object's
            # value is not None, or if the object's og value is falsy and the templates value is not
            if (
                getattr(obj, attr, None) in [[], {}, "", None]
                and template[attr] not in [[], {}, "", None]
            ):
                dict_obj[attr] = template[attr]

        # Create a new object out of the modified dict representation of the original object
        new_obj = obj_class(**dict_obj)

        # Now add all of the properties to the original object from the new object.
        # NOTE this allows us to return the exact same object that was passed as and
        # argument but with the modifications, there by maintaining the objects identity. 
        for attr in new_obj.dict().keys():
            if attr == "tasks":
                continue

            updated_value = getattr(new_obj, attr)
            if getattr(obj, attr) != updated_value:
                setattr(obj, attr, updated_value)

        return obj

