import operator as operatorlib

from typing import get_args

from owe_python_sdk.schema import (
    ComparisonOperator,
    LogicalOperator,
    MembershipOperator,
    ConditionalExpression,
    ConditionalExpressions
)


class ConditionalExpressionEvaluator:
    def __init__(self):
        self._comparison_operators = list(get_args(ComparisonOperator))
        self._logical_operators = list(get_args(LogicalOperator))
        self._membership_operators = list(get_args(MembershipOperator))

    def evaluate_all(self, conditions: ConditionalExpressions, ctx=None):
        evaluations = []
        for condition in conditions:
            evaluations.append(self.evaluate(condition, ctx=ctx))

        return all(evaluations)

    def evaluate(self, condition: ConditionalExpression, ctx=None):
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

    def _comparison(self, operator, operands):
        return getattr(operatorlib, operator)(operands[0], operands[1])

    def _membership(self, _, operands):
        return operands[0] in operands[1]
    
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

        
          
