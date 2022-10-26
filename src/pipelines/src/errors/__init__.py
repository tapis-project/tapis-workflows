from errors.base import WorkflowsBaseException

# An error that indicates something wrong with the workflow executor
# itself or its configuration and is not related to a users workflow 
# submission and execution. For example, loss of connection with K8s cluster,
# rabbitmq, etc.
class ApplicationError(WorkflowsBaseException):
    pass

class NoAvailableWorkers(ApplicationError):
    pass

class WorkerLimitExceed(ApplicationError):
    pass

class WorkflowTerminated(ApplicationError):
    def __init__(self, msg="Workflow Terminated"):
        ApplicationError.__init__(self, msg)


# Execution-related Non-application errors. Results from failures in task
# and pipeline executions–either from poorly configured task definitions, tasks entering
# into some failure mode cascading into a pipeline failure mode, etc
class ExecutionError(WorkflowsBaseException):
    pass

class PipelineExecutionError(ExecutionError):
    pass

class TaskExecutionError(ExecutionError):
    pass

# Programming errors. Errors that can only come about from erroneous code
class ProgrammingError(WorkflowsBaseException):
    pass

class InvalidFlavorError(ProgrammingError):
    pass
