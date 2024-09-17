from core.daos import WorkflowExecutorStateDAO


class ArgMapper:
    def __init__(self, dao: WorkflowExecutorStateDAO):
        self._dao = dao

    def get_value_by_key(self, key):
        arg = self._dao.get_state().ctx.args.get(key, None)
        if arg == None: return None
        return arg.value
    
    def get_all(self):
        return self._dao.get_state().ctx.args