import os

from core.daos import FileSystemDAO


class TaskOutputMapper:
    def __init__(self, dao: FileSystemDAO):
        self._dao = dao

    def get_by_output_dir_and_id(self, output_dir: str, output_id: str):
        # Construct the task output path
        task_output_path = os.path.join(output_dir, output_id)

        result = self._dao.get(task_output_path)

        return result
