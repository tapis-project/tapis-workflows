from core.daos import FileSystemDAO


class ArgValueFileMapper:
    def __init__(self, dao: FileSystemDAO):
        self._dao = dao

    def save(self, key, value):
        self._dao.write(key, value)