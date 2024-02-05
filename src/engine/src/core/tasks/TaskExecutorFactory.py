import logging

from owe_python_sdk.events import EventExchange
from core.tasks.BuildTaskExecutorResolver import build_task_executor_resolver
from core.tasks.executors.requesters.HTTP import HTTP
from core.tasks.executors.Function import Function
from core.tasks.executors.Application import Application
from errors.tasks import InvalidTaskTypeError


class TaskExecutorFactory:
    def build(self, task, ctx, exchange: EventExchange, plugins=[]):
        fn = getattr(self, f"_{task.type}", None)
        if fn != None:
            try:
                return fn(task, ctx, exchange, plugins)
            except Exception as e:
                raise Exception(f"Error initializing Task Executor: {e}")

        # No function found to initialize built-in task executors. Check
        # the plugins and return the task executor instance of the first class
        # found for the current task type
        for plugin in plugins:
            PluginTaskExecutorClass = plugin.task_executors.get(task.type, None)
            if PluginTaskExecutorClass == None:
                continue
            
            try:
                return PluginTaskExecutorClass(task, ctx, exchange, plugins=plugins)
            except Exception as e:
                raise Exception(f"Error initializing Task Executor plugin: {e}")
            
        # No task executors found with for the provided task type so
        # raise an error
        raise InvalidTaskTypeError(
            f"Task '{task.id}' uses task type '{task.type}' which does not exist.",
            hint=f"Update Task with id=={task.id} to have one of the following types: [image_build, container_run, request]",
        )

    def _image_build(self, task, ctx, exchange, plugins):
        # Returns a build executor for the specified image builder and
        # deployment type
        executor = build_task_executor_resolver.resolve(task)
        return executor(task, ctx, exchange, plugins=plugins)

    def _request(self, task, ctx, exchange, plugins):
        return HTTP(task, ctx, exchange, plugins=plugins)
    
    def _application(self, task, ctx, exchange, plugins):
        return Application(task, ctx, exchange, plugins=plugins)

    def _function(self, task, ctx, exchange, plugins):
        return Function(task, ctx, exchange, plugins=plugins)

task_executor_factory = TaskExecutorFactory()
