from errors.base import PipelinesBaseException


class InvalidTaskTypeError(PipelinesBaseException):
    pass


class MissingInitialTasksError(PipelinesBaseException):
    pass


class InvalidDependenciesError(PipelinesBaseException):
    pass


class CycleDetectedError(PipelinesBaseException):
    pass


class FailedTaskError(PipelinesBaseException):
    pass
