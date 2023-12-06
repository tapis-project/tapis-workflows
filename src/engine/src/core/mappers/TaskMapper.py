from core.daos import WorkflowExecutorStateDAO


class TaskMapper:
    def __init__(self, dao: WorkflowExecutorStateDAO):
        self._dao = dao

    def get_by_id(self, _id):
        task = next(
            filter(
                lambda task: task.id == _id,
                self._dao.get_state().tasks
            ),
            None
        )

        return task