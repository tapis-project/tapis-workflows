from core.mappers import EnvVarValueFileMapper


class EnvVarValueFileRepository:
    def __init__(self, mapper: EnvVarValueFileMapper):
        self._mapper = mapper

    def save(self, key, value):
        self._mapper.save(key, value)