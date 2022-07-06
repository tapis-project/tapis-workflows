class APIBaseException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"