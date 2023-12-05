from owe_python_sdk.schema import Operand

from core.workflows import ValueFromService


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
        key = operand.keys()[0]
        if key == "task_output":
            value = self._value_from_service.get_task_output_value_by_id(
                task_id=operand[key]["task_id"],
                _id=operand[key]["output_id"]
            )
            return value
        
        if key == "args":
            value = self._value_from_service.get_arg_value_by_key(
                operand[key]["args"]
            )
            return value
        
        if key == "env":
            value = self._value_from_service.get_env_value_by_key(
                operand[key]["args"]
            )
            return value