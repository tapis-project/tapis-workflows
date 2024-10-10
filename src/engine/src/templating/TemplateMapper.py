from typing import Union

from repositories import TemplateRepository
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

    def map(
            self,
            map_target: Union[Pipeline, Task],
            uses: Uses
        ) -> Union[Pipeline, Task]:
        """This method takes an object(Pipeline or Task object), and updates its
        attributes with the values found in the templates
        
        IMPORTANT NOTE:
        The map target object is modified and returned by this function, not a
        copy.
        """

        # Clone git repository specified on the pipeline.uses if exists
        try:
            template = self.template_repo.get_by_uses(uses)
        except Exception as e:
            raise Exception(f"Template mapping error: {e}")
        
        # Resolve which class the final object should have
        map_target_class = Pipeline
        if not issubclass(map_target.__class__, Pipeline):
            map_target_class = self.task_map_by_type.get(
                template.get("type", None),
                None
            )

        print(f"TYPE map_target_class: {map_target_class.__name__}")

        # Raise exception if no class could be resolved from the template
        if map_target_class == None:
            raise Exception(f"Invalid Template: Unable to resolve object type from Template. Task template object 'type' property must be one of {list(self.task_map_by_type.keys())} | Recieved: {template.get('type', 'None')}")

        # This temporty object will hold the updated values for the final
        # map target
        tmp_obj = map_target.dict()

        print(f"TYPE tmp_obj: {type(tmp_obj)}")

        # Create a dictionary of the map target object and map the properties of
        # the template onto the dictionary
        for attr in template.keys():
            # For pipelines only. Skip the tasks property as they should be
            # handled seperately in another call to the map method of the
            # Template mapper
            if attr == "tasks":
                continue

            # For task only. The template should specify the correct type. For
            # all other properties, that are not specified, we use that which in
            # enumerated in the template
            if attr == "type":
                tmp_obj["type"] = template.get(attr)
                continue

            # Get the map target value and the template value for a given attr
            map_target_value = getattr(map_target, attr, None)
            template_value = template[attr]

            # Default the tmp objects attr to the template's value for that attr
            tmp_obj[attr] = template_value

            # If map target value is None, set the tmp objects value to the
            # templates value for the given attr
            if map_target_value == None and template_value != None:
                tmp_obj[attr] = template_value
                continue

            if template_value == None:
                tmp_obj[attr] = map_target_value
                continue

            # TODO I do not thing this covers all cases well.
            # # For all cases in which the object value is falsy and the template
            # # value is NOT falsy, set the tmp object's attr to the template
            # # object's value for that attr
            # if (
            #     map_target_value in [[], {}, ""]
            #     and template_value not in [[], {}, ""]
            # ):
            #     tmp_obj[attr] = template_value

        # Create a new object out of the modified dict representation of the
        # map target object
        new_obj = map_target_class(**tmp_obj)

        # Now update all of the properties to the map target object from the new
        # object.
        # NOTE this allows us to return the exact same object that was passed as
        # and argument but with the modifications, thereby maintaining the
        # objects identity. 
        for attr in new_obj.dict().keys():
            if attr == "tasks":
                continue

            updated_value = getattr(new_obj, attr)
            if getattr(map_target, attr, None) != updated_value:
                setattr(map_target, attr, updated_value)

        return map_target

