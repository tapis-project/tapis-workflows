from mappers import TaskMapper


class TaskRepository:
    def __init__(self, mapper: TaskMapper):
        self._mapper = mapper

    def get_by_id(self, _id):
        task = self._mapper.get_by_id(_id)
        return task