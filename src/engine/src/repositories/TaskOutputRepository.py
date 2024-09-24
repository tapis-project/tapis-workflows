from mappers import TaskOutputMapper

from owe_python_sdk.schema import Task


class TaskOutputRepository:
    def __init__(
            self,
            mapper: TaskOutputMapper
        ):
        self._mapper = mapper

    def get_output_by_task_and_id(self, task: Task, output_id):
        output = self._mapper.get_by_output_dir_and_id(task.output_dir, output_id)
        return output