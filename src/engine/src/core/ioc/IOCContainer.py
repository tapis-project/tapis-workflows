class IOCContainer:
    def __init__(self):
        self._configurations = {}
        self._cache = {}

    def register(self, key, handler: callable, as_singleton=False):
        self._configurations[key] = {
            "handler": handler,
            "as_singleton": as_singleton
        }

    # NOTE *args and **kwargs not really implemented in handlers, but good
    # to leave it for extensibility. Perhaps in the future, we may want the object
    # loading to be configurable.
    def load(self, key):
        if key in self._cache:
            return self._cache[key]
        
        configuration = self._configurations.get(key, None)
        if configuration == None:
            raise Exception(f"No object registered with key {key}")

        obj = configuration["handler"]()
        if configuration["as_singleton"]:
            self._cache[key] = obj 
            
        return obj



