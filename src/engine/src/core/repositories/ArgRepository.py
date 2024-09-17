from core.mappers import ArgMapper


class ArgRepository:
    def __init__(self, mapper: ArgMapper):
        self._mapper = mapper

    def get_value_by_key(self, key):
        value = self._mapper.get_value_by_key(key)
        return value
    
    def get_all(self):
        return self._mapper.get_all()