from typing import List

from owe_python_sdk.Plugin import Plugin
from repositories import (
    TaskOutputRepository,
    TaskRepository,
    EnvRepository,
    ArgRepository
)

class ValueFromService:
    def __init__(
            self,
            task_repo: TaskRepository,
            task_output_repo: TaskOutputRepository,
            arg_repo: ArgRepository,
            env_repo: EnvRepository,
            plugins: List[Plugin] = []
        ):
        self._task_repo = task_repo
        self._task_output_repo = task_output_repo
        self._arg_repo = arg_repo
        self._env_repo = env_repo
        self._plugins = plugins

    def get_task_output_value_by_id(self, task_id, _id):
        task = self._task_repo.get_by_id(task_id)
        output = self._task_output_repo.get_output_by_task_and_id(task, _id)
        return output
    
    def get_env_value_by_key(self, key):
        value = self._env_repo.get_value_by_key(key)
        return value
    
    def get_arg_value_by_key(self, key):
        value = self._arg_repo.get_value_by_key(key)
        return value
    
    def get_args(self):
        return self._arg_repo.get_all()
    
    # Finds the first secrets engine from plugins and fetches the secret
    def get_secret_value_by_engine_and_pk(self, engine, pk):
        plugin = next(filter(
            lambda p: engine in p.engines,
            self._plugins
        ))
        secrets_engine = plugin.engines[engine]
        return secrets_engine(pk, self._arg_repo.get_all())