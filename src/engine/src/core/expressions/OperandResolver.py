from owe_python_sdk.schema import Operand

from core.workflows import ValueFromService
from errors.tasks import OperandResolutionError


class OperandResolver:
    def __init__(
        self,
        value_from_service: ValueFromService
    ):
        self._value_from_service = value_from_service

    def resolve(self, operand: Operand):
        if type(operand) != dict:
            return operand
        
        # NOTE all operands should have only 1 key
        key = list(operand.keys())[0]
        if key == "task_output":
            try:
                value = self._value_from_service.get_task_output_value_by_id(
                    task_id=operand[key].task_id,
                    _id=operand[key].output_id
                )

                return value
            except Exception:
                raise OperandResolutionError(f"No output found for task '{operand[key].task_id}' with output id of '{operand[key].output_id}'")
        
        if key == "args":
            try:
                print(f"GETTING VALUE FROM ARG '{operand[key]}'")
                value = self._value_from_service.get_arg_value_by_key(
                    operand[key]
                )
                return value
            except Exception:
                raise OperandResolutionError(f"Error attempting to fetch value from args at key '{key}'")
        
        if key == "env":
            try:
                value = self._value_from_service.get_env_value_by_key(
                    operand[key]
                )
                return value
            except Exception:
                raise OperandResolutionError(f"Error attempting to fetch value from env at key '{key}'")