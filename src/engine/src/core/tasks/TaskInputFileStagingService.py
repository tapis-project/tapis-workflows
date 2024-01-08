import os

from core.workflows import ValueFromService
from owe_python_sdk.schema import Task
from errors.tasks import TaskInputStagingError


class TaskInputFileStagingService:
    """Responsible for creating the actual files that will be used as inputs
    during a task execution. Possible sources of data for the input files may be
    one or all of the following:
    1) The value property of an input specification
    2) An argument passed as part of a pipeline invocation
    2) A variable from the envrionment with which the pipeline was invoked
    2) An output file from another task upon which the staging task is dependent
    """
    def __init__(
        self,
        value_from_service: ValueFromService
    ):
        self._value_from_service = value_from_service
    
    # TODO Improve error handling below. Catch specific errors from the value from service
    def stage(self, task: Task):
        """Iterates over all of the items in the task input dictionary, fetches
        the values from their sources, then creates the files in the task's 
        working directory"""
        for input_id, input_ in task.input.items():
            if input_.value != None:
                self._create_input_(task, input_id, input_.value)
                continue
            
            value = None
            value_from = input_.value_from
            key = list(value_from.keys())[0] # NOTE Should only have 1 key
            if key == "task_output":
                try:
                    value = self._value_from_service.get_task_output_value_by_id(
                        task_id=value_from[key].task_id,
                        _id=value_from[key].output_id
                    )
                except Exception as e:
                    if input_.required:
                        raise TaskInputStagingError(f"No output found for task '{value_from[key].task_id}' with output id of '{value_from[key].output_id}' | {e}")
            if key == "args":
                try:
                    value = self._value_from_service.get_arg_value_by_key(
                        value_from[key]
                    )
                except Exception as e:
                    if input_.required:
                        raise TaskInputStagingError(f"Error attempting to fetch value from args at key '{value_from[key]}' | {e}")
            if key == "env":
                try:
                    value = self._value_from_service.get_env_value_by_key(
                        value_from[key]
                    )
                except Exception as e:
                    if input_.required:
                        raise TaskInputStagingError(f"Error attempting to fetch value from env at key '{value_from[key]}' | {e}")
                
            self._create_input_(task, input_id, value)

    def _create_input_(self, task, input_id, value):
        try:
            with open(os.path.join(task.input_dir, input_id), mode="w") as file:
                if value == None: value = ""
                print(f"WRITING {input_id} |", type(value), "|", value)
                file.write(str(value))
        except Exception as e:
            raise TaskInputStagingError(f"Error while staging input: {e}") 

        

            