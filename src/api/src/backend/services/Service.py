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

    def _register_service(self, name, service_cls):
        self.services[name] = service_cls
    
    def _get_service(self, name):
        return self.service[name]()

