from core.repositories import (
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
            env_repo: EnvRepository
        ):
        self._task_repo = task_repo
        self._task_output_repo = task_output_repo
        self._arg_repo = arg_repo
        self._env_repo = env_repo

    def get_task_output_value_by_id(self, task_id, _id):
        task = self._task_repo.get_by_id(task_id)
        output = self._task_output_repo.get_output_by_task_and_id(task, _id)
        return output
    
    def get_env_value_by_key(self, key):
        output = self._env_repo.get_by_key(key)
        return output
    
    def get_arg_value_by_key(self, key):
        output = self._arg_repo.get_by_key(key)
        return output
        