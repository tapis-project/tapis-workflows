from typing import List

from owe_python_sdk.Plugin import Plugin
from core.ioc import IOCContainer
from core.state import ReactiveState
from core.daos import (
    WorkflowExecutorStateDAO,
    FileSystemDAO
)
from core.mappers import (
    ArgMapper,
    ArgValueFileMapper,
    EnvMapper,
    EnvVarValueFileMapper,
    TaskMapper,
    TaskOutputMapper
)
from core.repositories import (
    ArgRepository,
    ArgValueFileRepository,
    EnvRepository,
    EnvVarValueFileRepository,
    GitCacheRepository,
    TaskOutputRepository,
    TaskRepository,
    TemplateRepository
)
from core.tasks.TaskInputFileStagingService import TaskInputFileStagingService
from core.workflows import (
    GraphValidator,
    ValueFromService
)
from core.expressions import (
    ConditionalExpressionEvaluator,
    OperandResolver
)

class IOCContainerFactory:
    def build(self, plugins: List[Plugin] = []):
        container = IOCContainer()

        container.register("ReactiveState",
            lambda: ReactiveState(),
            as_singleton=True
        )

        container.register("WorkflowExecutorStateDAO",
            lambda: WorkflowExecutorStateDAO(
                container.load("ReactiveState")
            )
        )

        container.register("FileSystemDAO",
            lambda: FileSystemDAO()
        )

        container.register("ArgMapper",
            lambda: ArgMapper(
                container.load("WorkflowExecutorStateDAO")
            )
        )

        container.register("ArgValueFileMapper",
            lambda: ArgValueFileMapper(
                container.load("FileSystemDAO")
            )
        )

        container.register("EnvMapper",
            lambda: EnvMapper(
                container.load("WorkflowExecutorStateDAO")
            )
        )

        container.register("EnvVarValueFileMapper",
            lambda: EnvVarValueFileMapper(
                container.load("FileSystemDAO")
            )
        )

        container.register("TaskMapper",
            lambda: TaskMapper(
                container.load("WorkflowExecutorStateDAO")
            )
        )

        container.register("TaskOutputMapper",
            lambda: TaskOutputMapper(
                container.load("FileSystemDAO")
            )
        )

        container.register("ArgRepository",
            lambda: ArgRepository(
                container.load("ArgMapper")
            )
        )

        container.register("ArgValueFileRepository",
            lambda: ArgValueFileRepository(
                container.load("ArgValueFileMapper")
            )
        )

        container.register("EnvRepository",
            lambda: EnvRepository(
                container.load("EnvMapper")
            )
        )

        container.register("EnvVarValueFileRepository",
            lambda: EnvVarValueFileRepository(
                container.load("EnvVarValueFileMapper")
            )
        )

        # TODO Uncomment after GitCacheRepository refactor
        # container.register("GitCacheRepository",
        #     lambda: GitCacheRepository(
        #         container.load("GitCacheMapper")
        #     )
        # )

        container.register("TaskInputFileStagingService",
            lambda: TaskInputFileStagingService(
                container.load("ValueFromService")
            )
        )

        container.register("TaskOutputRepository",
            lambda: TaskOutputRepository(
                container.load("TaskOutputMapper")
            )
        )

        container.register("TaskRepository",
            lambda: TaskRepository(
                container.load("TaskMapper")
            )
        )

        # TODO Uncomment after TemplateRepository refactor
        # container.register("TemplateRepository",
        #     lambda: TemplateRepository(
        #         container.load("TemplateMapper")
        #     )
        # )

        container.register("GraphValidator",
            lambda: GraphValidator()
        )

        container.register("ValueFromService",
            lambda: ValueFromService(
                container.load("TaskRepository"),
                container.load("TaskOutputRepository"),
                container.load("ArgRepository"),
                container.load("EnvRepository"),
                plugins=plugins if len(plugins) > 0 else []
            )
        )

        container.register("OperandResolver",
            lambda: OperandResolver(
                container.load("ValueFromService")
            )
        )

        container.register("ConditionalExpressionEvaluator",
            lambda: ConditionalExpressionEvaluator(
                container.load("OperandResolver")
            )
        )

        return container

