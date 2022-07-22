from core.BuildTaskExecutorResolver import build_task_executor_resolver
from core.TaskExecutor import TaskExecutor
from executors.Request import Request
from errors.tasks import InvalidTaskTypeError


class TaskExecutorFactory:
    def build(self, task, message) -> TaskExecutor:
        try:
            fn = getattr(self, f"_{task.type}")
        except AttributeError:
            raise InvalidTaskTypeError(
                f"Task '{task.name}' uses task type '{task.type}' which does not exist.",
                hint=f"Update Task with id=={task.id} to have one of the following types: [image_build, container_run, request]",
            )

        return fn(task, message)

    def _image_build(self, task, message) -> TaskExecutor:
        # Returns a build executor for the specified image builder and
        # deployment type
        executor = build_task_executor_resolver.resolve(task)
        return executor(task, message)

    def _request(self, task, message) -> TaskExecutor:
        return Request(task, message)

    def _container_run(self, task, message) -> TaskExecutor:
        return Request(task, message)


task_executor_factory = TaskExecutorFactory()
