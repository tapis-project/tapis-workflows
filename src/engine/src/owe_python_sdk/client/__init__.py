from __future__ import annotations

import os
from getpass import getpass

from typing import List

from owe_python_sdk import schema as owe_schema


class Runnable:
    def _set_runner(self, runner: Runner=None):
        if runner != None and not isinstance(runner):
            raise Exception("Runner must implement the 'Runner' class")

        self.runner = runner

class Task(Runnable):
    def __init__(self, schema: dict, runner: Runner=None):
        self._set_runner(runner)
        self.schema = owe_schema.BaseTask(**schema)

    def depends_on(self, task: Task, *tasks: List[Task], can_fail=False) -> None:
        dependencies = [task, *tasks]
        for dep in dependencies:
            if type(dep) != Task:
                raise TypeError(f"Task dependencies must be of type {self.__class__.__name__} | Recieved {type(dep)}")

            self.schema.depends_on.append(owe_schema.TaskDependency({
                "id": dep.id,
                "can_fail": can_fail
            }))

class Pipeline(Runnable):
    def __init__(self, schema: dict, runner: Runner=None):
        self.schema = owe_schema.BasePipeline(**schema)
        self.runner = runner

    def add_task(self, task: Task, *tasks: List[Task]):
        new_tasks = [task, *tasks]
        for new_task in new_tasks:
            if type(new_task) != Task:
                raise TypeError(f"Task dependencies must be of type Task | Recieved {type(new_task)}")
            
            self.schema.tasks.append(new_task.schema)

    def start(self):
        if self.runner == None:
            raise Exception("No Runner found")

        self.runner.submit(self.schema.dict())

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

    def submit(self):
        raise NotImplementedError(f"Runner class {type(self)} does not implement the 'submit' method")

    class Config:
        prompt_missing = False
        env = {}


    