from backend.errors.base import APIBaseException

class AuthenticationError(APIBaseException):
    pass

class BadRequestError(APIBaseException):
    pass

class AccessForbiddenError(APIBaseException):
    pass
        
class UnprocessableEntityError(APIBaseException):
    pass

class NotFoundError(APIBaseException):
    pass

class ServerError(APIBaseException):
    pass