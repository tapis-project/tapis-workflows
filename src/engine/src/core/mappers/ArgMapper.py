from core.daos import WorkflowExecutorStateDAO


class ArgMapper:
    def __init__(self, dao: WorkflowExecutorStateDAO):
        self._dao = dao

    def get_value_by_key(self, key):
        arg = self._dao.get_state().ctx.args.get(key, None)
        print(f"GETTING VALUE FOR ARG {key}:", arg)
        if arg == None: return None
        return arg.value