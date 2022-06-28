from errors.base import PipelinesBaseException


class InvalidActionTypeError(PipelinesBaseException):
    pass


class MissingInitialActionsError(PipelinesBaseException):
    pass


class InvalidDependenciesError(PipelinesBaseException):
    pass


class CycleDetectedError(PipelinesBaseException):
    pass


class FailedActionError(PipelinesBaseException):
    pass
