from core.mappers import EnvMapper


class EnvRepository:
    def __init__(self, mapper: EnvMapper):
        self._mapper = mapper

    def get_value_by_key(self, key):
        value = self._mapper.get_value_by_key(key)
        return value
