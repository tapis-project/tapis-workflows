from functools import partial

from core.ioc import IOCContainer
from core.state import ReactiveState
from core.daos import (
    WorkflowExecutorStateDAO,
    FileSystemDAO
)
from core.mappers import (
    ArgMapper,
    EnvMapper,
    TaskMapper,
    TaskOutputMapper
)
from core.repositories import (
    ArgRepository,
    EnvRepository,
    GitCacheRepository,
    TaskOutputRepository,
    TaskRepository,
    TemplateRepository
)
from core.workflows import (
    GraphValidator,
    ValueFromService
)
from core.expressions import (
    ConditionalExpressionEvaluator,
    OperandResolver
)

class IOCContainerFactory:
    def build(self):
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

        container.register("EnvMapper",
            lambda: EnvMapper(
                container.load("WorkflowExecutorStateDAO")
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

        container.register("EnvRepository",
            lambda: EnvRepository(
                container.load("EnvMapper")
            )
        )

        # TODO Uncomment after GitCacheRepository refactor
        # container.register("GitCacheRepository",
        #     lambda: GitCacheRepository(
        #         container.load("GitCacheMapper")
        #     )
        # )

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
                container.load("EnvRepository")
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

