from backend.errors.base import APIBaseException

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