class CICDBaseException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"{self.__class__.name}: {self.message}"

class CredentialError(CICDBaseException):
    pass
