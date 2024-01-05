from core.daos import WorkflowExecutorStateDAO


class EnvMapper:
    def __init__(self, dao: WorkflowExecutorStateDAO):
        self._dao = dao

    def get_value_by_key(self, key):
        env = self._dao.get_state().ctx.env.get(key, None)
        if env == None: return None
        return env.value