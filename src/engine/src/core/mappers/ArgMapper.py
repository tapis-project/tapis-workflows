from core.daos import WorkflowExecutorStateDAO


class ArgMapper:
    def __init__(self, dao: WorkflowExecutorStateDAO):
        self._dao = dao

    def get_value_by_key(self, key):
        value = self._dao.get_state().ctx.args.get(key).value
        return value