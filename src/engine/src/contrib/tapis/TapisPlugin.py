from owe_python_sdk.Plugin import Plugin
from owe_python_sdk.SchemaExtension import SchemaExtension
from contrib.tapis.middleware.request import (
    ValueFromTapisSecurityKernal,
    ParamsValidator
)
from contrib.tapis.executors import TapisActor, TapisJob
from contrib.tapis.constants import TASK_TYPE_TAPIS_ACTOR, TASK_TYPE_TAPIS_JOB


class TapisPlugin(Plugin):
    def __init__(self, name):
        Plugin.__init__(self, name)
        
        self.register("request", ValueFromTapisSecurityKernal())
        self.register("request", ParamsValidator())
        self.register("task_executor", {TASK_TYPE_TAPIS_ACTOR: TapisActor})
        self.register("task_executor", {TASK_TYPE_TAPIS_JOB: TapisJob})
        self.register("schema_extension", SchemaExtension(
            _type="task_executor",
            sub_type="function",
            schema={
                "runtimes": {
                    "python": ["tapis/workflows-python-singularity:0.1.0"]
                }
            }
        ))