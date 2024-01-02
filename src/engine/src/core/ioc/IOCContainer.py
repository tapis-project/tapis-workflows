class IOCContainer:
    def __init__(self):
        self._configurations = {}
        self._cache = {}

    # Adds the handler that will be return - and if specified, cache - an
    # instance of a class 
    def register(self, key, handler: callable, as_singleton=False):
        self._configurations[key] = {
            "handler": handler,
            "as_singleton": as_singleton
        }

    # Loads an instance from the cache if registered as a singleton, or 
    # instantiates a new object by calling the registered handler
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



