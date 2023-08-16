from owe_python_sdk.Plugin import Plugin
from owe_python_sdk.SchemaExtension import SchemaExtension
from owe_python_sdk.NotificationMiddleware import NotificationMiddleware
from owe_python_sdk.ArchiveMiddleware import ArchiveMiddleware
from owe_python_sdk.events.types import (
    PIPELINE_ACTIVE, PIPELINE_COMPLETED, PIPELINE_ARCHIVING, PIPELINE_FAILED,
    PIPELINE_PENDING, PIPELINE_SUSPENDED, PIPELINE_TERMINATED, TASK_ACTIVE,
    TASK_ARCHIVING, TASK_BACKOFF, TASK_COMPLETED, TASK_FAILED, TASK_PENDING,
    TASK_SUSPENDED, TASK_TERMINATED
)


from contrib.tapis.middleware.request import (
    ValueFromTapisSecurityKernal,
    ParamsValidator
)
from contrib.tapis.middleware.event_handlers.archivers import TapisSystemArchiver
from contrib.tapis.middleware.event_handlers.notifications import TapisWorkflowsAPIBackend
from contrib.tapis.executors import TapisActor, TapisJob
from contrib.tapis.constants import TASK_TYPE_TAPIS_ACTOR, TASK_TYPE_TAPIS_JOB, ARCHIVER_TYPE_TAPIS_SYSTEM


class TapisPlugin(Plugin):
    def __init__(self, name):
        Plugin.__init__(self, name)
        
        self.register("request", ValueFromTapisSecurityKernal())
        self.register("request", ParamsValidator())
        self.register(
            "notification_handler",
            NotificationMiddleware(
                handler=TapisWorkflowsAPIBackend,
                subscriptions=[
                    PIPELINE_ACTIVE, PIPELINE_COMPLETED, PIPELINE_ARCHIVING, PIPELINE_FAILED,
                    PIPELINE_PENDING, PIPELINE_SUSPENDED, PIPELINE_TERMINATED, TASK_ACTIVE,
                    TASK_ARCHIVING, TASK_BACKOFF, TASK_COMPLETED, TASK_FAILED, TASK_PENDING,
                    TASK_SUSPENDED, TASK_TERMINATED
                ]
            )
        )
        self.register(
            "archive",
            ArchiveMiddleware(
                ARCHIVER_TYPE_TAPIS_SYSTEM,
                handler=TapisSystemArchiver,
                subsciptions=[PIPELINE_COMPLETED, PIPELINE_FAILED, PIPELINE_TERMINATED]
            )
        )
        self.register("task_executor", {TASK_TYPE_TAPIS_ACTOR: TapisActor})
        self.register("task_executor", {TASK_TYPE_TAPIS_JOB: TapisJob})
        self.register("schema_extension", SchemaExtension(
            _type="task_executor",
            sub_type="function",
            schema={
                "runtimes": {
                    "python": [
                        "tapis/workflows-python-singularity:0.1.0",
                        "tapis/flaskbase:1.2.2"
                    ]
                }
            }
        ))