from mappers import ArgValueFileMapper


class ArgValueFileRepository:
    def __init__(self, mapper: ArgValueFileMapper):
        self._mapper = mapper

    def save(self, key, value):
        self._mapper.save(key, value)