from errors.base import CICDBaseException


class InvalidActionTypeError(CICDBaseException):
    pass


class MissingInitialActionsError(CICDBaseException):
    pass


class InvalidDependenciesError(CICDBaseException):
    pass


class CycleDetectedError(CICDBaseException):
    pass


class FailedActionError(CICDBaseException):
    pass
