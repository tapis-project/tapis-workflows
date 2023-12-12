import operator as operatorlib

from typing import get_args

from owe_python_sdk.schema import (
    ComparisonOperator,
    LogicalOperator,
    MembershipOperator,
    ConditionalExpression,
    ConditionalExpressions
)
from core.expressions import OperandResolver
from errors.tasks import ConditionalExpressionEvalError, OperandResolutionError


class ConditionalExpressionEvaluator:
    def __init__(
            self,
            operand_resolver: OperandResolver
        ):
        self._comparison_operators = list(get_args(ComparisonOperator))
        self._logical_operators = list(get_args(LogicalOperator))
        self._membership_operators = list(get_args(MembershipOperator))
        self._operand_resolver = operand_resolver

    def evaluate_all(self, conditions: ConditionalExpressions):
        evaluations = []
        for condition in conditions:
            evaluations.append(self.evaluate(condition))

        return all(evaluations)

    def evaluate(self, condition: ConditionalExpression):
        try:
            operator = list(condition.keys())[0] # There will only ever be one key in a condition.
            operands = condition[operator]
            if operator in self._comparison_operators:
                return self._comparison(operator, operands)

            if operator in self._membership_operators:
                return self._membership(operator, operands)
            
            if operator == "not":
                return not self.evaluate(operands)
                
            if operator in self._logical_operators:
                return self._logical(operator, operands)
        except OperandResolutionError as e:
            raise ConditionalExpressionEvalError(str(e))

    def _comparison(self, operator, operands):
        resolved_operands = [
            self._operand_resolver.resolve(operand)
            for operand in operands 
        ]
        return getattr(operatorlib, operator)(resolved_operands[0], resolved_operands[1])

    def _membership(self, _, operands):
        resolved_needle = self._operand_resolver.resolve(operands[0])
        resolved_haystack = [
            self._operand_resolver.resolve(operand)
            for operand in operands[1]
        ]
        return resolved_needle in resolved_haystack
    
    def _logical(self, operator, operands):
        evaluations = []
        for condition in operands:
            evaluations.append(self.evaluate(condition))

        if operator == "and":
            return all(evaluations)
        if operator == "or":
            return any(evaluations)
        if operator == "xor": 
            return not all(evaluations) and not all([not e for e in evaluations])
        if operator == "nand":
            return not all(evaluations)
        if operator == "nor":
            return all([not e for e in evaluations])
        if operator == "xnor":
            return all(evaluations) or all([not e for e in evaluations])

        
          
