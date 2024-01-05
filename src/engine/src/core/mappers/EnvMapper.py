from core.daos import WorkflowExecutorStateDAO


class EnvMapper:
    def __init__(self, dao: WorkflowExecutorStateDAO):
        self._dao = dao

    def get_value_by_key(self, key):
        print("ENVMAPPER")
        print("KEY", key)
        print("KEY ON ENV", self._dao.get_state().ctx.env.get(key))
        env = self._dao.get_state().ctx.env.get(key).value
        if env == None: return None
        return env.value