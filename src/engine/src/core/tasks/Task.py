from core.tasks.TaskExecutorFactory import task_executor_factory as factory


class Task:
    def __init__(self, task, ctx, exchange):
        for key, val in task.__dict__.items():
            setattr(self, key, val)

        self._executor = factory.build(task, ctx, exchange)

    def __call__(self,):
        return self._executor.execute()