from base import CICDBaseException

class BadRequestError(CICDBaseException):
    pass

class AccessForbiddenError(CICDBaseException):
    pass
        
class UnprocessableEntityError(CICDBaseException):
    pass

class NotFoundError(CICDBaseException):
    pass