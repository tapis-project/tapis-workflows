from owe_python_sdk.Plugin import Plugin
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