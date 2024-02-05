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