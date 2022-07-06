from functools import partial


class Service:
    def __init__(self):
        self.rollbacks = []
        self.services = {}
    
    def rollback(self):
        for rollback in self.rollbacks:
            try:
                rollback()
            except Exception as e:
                pass

    def _add_rollback(self, fn, *args, **kwargs):
        self.rollbacks.append(partial(fn, *args, **kwargs))

