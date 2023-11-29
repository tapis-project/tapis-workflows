from functools import partial


class Service:
    def __init__(self):
        self.errors: list[str] = []
        self.rollbacks = []
        self.services = {}
    
    def rollback(self, raise_exception=False):
        success = True
        for rollback in self.rollbacks:
            try:
                rollback()
            except Exception as e:
                success = False
                self.errors.append(str(e))
                if raise_exception:
                    raise e

        return success

    def _add_rollback(self, fn, *args, **kwargs):
        self.rollbacks.append(partial(fn, *args, **kwargs))

