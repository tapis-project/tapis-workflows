from __future__ import annotations

import os
from getpass import getpass

from typing import List

import schema as owe_schema

from utils import adapt_runner, override_runner_configs
from errors import RunnerAdaptationError


class Runnable:
    def _set_runner_class(
        self,
        runner_class: Runner=None,
        runner_config_override={},
    ):
        # Try to adapt the runner class if provided instance of runner
        # does not inherit from Runner
        self.runner_class = None
        try:
            if runner_class != None and not issubclass(runner_class, Runner):
                runner_class = adapt_runner(Runner, runner_class)
        except Exception as e:
            raise RunnerAdaptationError(f"Failed to adapt provided runner instance. Try using the 'adapt_runner' utility on the provided runner class before registering it with tasks and pipelines | Error: {e}")

        if runner_class == None:
            return

        self.runner_class = override_runner_configs(runner_class, runner_config_override)

class Task(Runnable):
    def __init__(
        self,
        schema: dict,
        runner_class: Runner=None,
        runner_config_override={}
    ):
        self._set_runner_class(runner_class, runner_config_override=runner_config_override)
        self.schema = owe_schema.BaseTask(**schema)

    def depends_on(self, task: Task, *tasks: List[Task], can_fail=False) -> None:
        dependencies = [task, *tasks]
        for dep in dependencies:
            if type(dep) != Task:
                raise TypeError(f"Task dependencies must be of type {self.__class__.__name__} | Recieved {type(dep)}")

            self.schema.depends_on.append(
                owe_schema.TaskDependency(**{
                    "id": dep.schema.id,
                    "can_fail": can_fail
                })
            )

class Pipeline(Runnable):
    def __init__(
        self,
        schema: dict,
        runner_class: Runner,
        runner_config_override={}
    ):
        self.schema = owe_schema.BasePipeline(**schema)
        self._set_runner_class(runner_class, runner_config_override=runner_config_override)

    def add_task(self, task: Task, *tasks: List[Task]):
        new_tasks = [task, *tasks]
        for new_task in new_tasks:
            if type(new_task) != Task:
                raise TypeError(f"Task dependencies must be of type Task | Recieved {type(new_task)}")
            
            self.schema.tasks.append(new_task.schema)

    def start(self,
        params: owe_schema.KeyVal={},
        runner_args=[],
        runner_kwargs={},
    ):
        if self.runner_class == None:
            raise Exception("Missing Runner: No Runner specified for this Pipeline")

        self.runner = self.runner_class(*runner_args, **runner_kwargs)
        self.runner.submit({"pipeline": self.schema.dict(), "params": params})

class Runner:
    def __init__(self):
        self.env = {}
        for var, var_spec in self.Config.env.items():
            if type(var_spec) != dict:
                raise TypeError("Environment variable spec must be a dictionary")

            value = os.environ.get(var, None)
            if value != None:
                self.env[var] = var_spec.get("type", str)(value)
                continue

            if self.Config.prompt_missing == False:
                raise Exception(f"Cannot find variable {var} in envrionement")
            
            prompt = input
            if var_spec.get("secret", False):
                prompt = getpass

            value = prompt(f"{var}: ")

            if value == "":
                raise Exception(f"Variable {var} requires a value")

            self.env[var] = var_spec.get("type", str)(value)

    def submit(self, request, *_, **__):
        raise NotImplementedError(f"Runner class {type(self)} does not implement the 'submit' method")

    class Config:
        prompt_missing = False
        env = {}