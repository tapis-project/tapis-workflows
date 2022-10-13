from errors.base import WorkflowsBaseException


class InvalidTaskTypeError(WorkflowsBaseException):
    pass


class MissingInitialTasksError(WorkflowsBaseException):
    pass


class InvalidDependenciesError(WorkflowsBaseException):
    pass


class CycleDetectedError(WorkflowsBaseException):
    pass


class FailedTaskError(WorkflowsBaseException):
    pass
