import os

from importlib.util import find_spec
from importlib import import_module

from errors.builder import InvalidBuilderError


class BuildTaskExecutorResolver:
    def __init__(self):
        self.deployment_type = self._to_class_name(os.environ["DEPLOYMENT_TYPE"])

    def resolve(self, task):
        builder_name = task.builder
        builder_ns = f"core.executors.builders.{builder_name}"

        if bool(find_spec(builder_ns)):
            module = import_module(f"{builder_ns}.{self.deployment_type}", "./")
            return getattr(module, self.deployment_type)

        raise InvalidBuilderError(
            f"Build '{builder_name}' is not a valid image builder."
        )

    def _to_class_name(self, string: str):
        return string.lower().capitalize()


build_task_executor_resolver = BuildTaskExecutorResolver()
