from core.BuildTaskExecutorResolver import build_task_executor_resolver
from core.TaskExecutor import TaskExecutor
from core.events import EventExchange
from core.executors.Request import Request
from errors.tasks import InvalidTaskTypeError


class TaskExecutorFactory:
    def build(self, task, ctx, exchange: EventExchange) -> TaskExecutor:
        try:
            fn = getattr(self, f"_{task.type}")

            return fn(task, ctx, exchange)
        except AttributeError:
            raise InvalidTaskTypeError(
                f"Task '{task.name}' uses task type '{task.type}' which does not exist.",
                hint=f"Update Task with id=={task.id} to have one of the following types: [image_build, container_run, request]",
            )
        except Exception as e:
            raise Exception(f"Error initializing Task Executor: {e}")

    def _image_build(self, task, ctx, exchange) -> TaskExecutor:
        # Returns a build executor for the specified image builder and
        # deployment type
        executor = build_task_executor_resolver.resolve(task)
        return executor(task, ctx, exchange)

    def _request(self, task, ctx, exchange) -> TaskExecutor:
        return Request(task, ctx, exchange)

    def _container_run(self, task, ctx, exchange) -> TaskExecutor:
        return Request(task, ctx, exchange)
    
    def _function(self, task, ctx, exchange) -> TaskExecutor:
        return Request(task, ctx, exchange)

    def _tapis_job(self, task, ctx, exchange) -> TaskExecutor:
        return Request(task, ctx, exchange)

    def _tapis_actor(self, task, ctx, exchange) -> TaskExecutor:
        return Request(task, ctx, exchange)

task_executor_factory = TaskExecutorFactory()
