from typing import Union, List


def adapt_runner(Runner, RunnerClassExtension: type):
    def __init__(self, *args, **kwargs):
        Runner.__init__(self)
        RunnerClassExtension.__init__(self, *args, **kwargs)

    # Raise Exception if RunnerClassExtension does not have a
    # Config property
    if not hasattr(RunnerClassExtension, "Config"):
        raise AttributeError(f"Runner class '{RunnerClassExtension.__name__}' is missing a Config class")

    AdaptedRunner = type(
        "AdaptedRunner",
        (RunnerClassExtension, Runner),
        {"__init__": __init__}
    )

    return AdaptedRunner

def override_runner_configs(runner_class: type, config_override: dict):
    # Override the config on the RunnerClassExtension
    for key, val in config_override.items():
        setattr(runner_class.Config, key, val)

    return runner_class

def get_schema_extensions(plugins, _type, sub_type=None):
    schema_extensions = []
    for plugin in plugins:
        schema_extensions = schema_extensions + [ 
            ext.schema for ext in plugin.schema_extensions 
            if ext.type == _type 
            and (ext.sub_type == sub_type or sub_type == None)
        ]

    return schema_extensions

def select_key_or_index(target: Union[dict, list], key_or_index: Union[str, int]):
    if type(target) == list:
        return target[int(key_or_index)]

    if type(target) == dict:
        return target[key_or_index]
    
    raise TypeError("Argument `target` must be of type `dict` or `list`")


def select_field(obj: Union[dict, list], selectors: list[str] = []):
    if len(selectors) == 0:
        return obj
    
    selector = selectors[0]
    if len(selectors) == 1:
        return select_key_or_index(obj, selector)
    
    selected_obj = select_key_or_index(obj, selector)
    return select_field(selected_obj, selectors[1:])