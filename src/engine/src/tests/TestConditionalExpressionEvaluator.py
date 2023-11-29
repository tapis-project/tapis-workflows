import unittest

from helpers.ConditionalExpressionEvaluator import ConditionalExpressionEvaluator
from tests.fixtures.conditional_expressions import (
    and_true,
    and_false,
    not_op_true,
    not_op_false,
    or_true,
    or_false,
    xor_true,
    xor_false1,
    xor_false2,
    xnor_true1,
    xnor_true2,
    xnor_false,
    nor_true,
    nor_false1,
    nor_false2,
    in_true,
    in_false,
    comparison_true,
    comparison_false,
    nested_and_true,
    nested_and_false,
    nested_and_or_true,
    nested_and_or_false,
)


class TestConditionalExpressionEvaluator(unittest.TestCase):
    def setUp(self):
        self.evaluator = ConditionalExpressionEvaluator()

    def testEvaluateCompare(self):
        # comparison
        self.assertTrue(self.evaluator.evaluate(comparison_true))
        self.assertFalse(self.evaluator.evaluate(comparison_false))

    def testEvaluateAnd(self):
        # and
        self.assertTrue(self.evaluator.evaluate(and_true))
        self.assertFalse(self.evaluator.evaluate(and_false))

    def testEvaluateNot(self):
        # not
        self.assertTrue(self.evaluator.evaluate(not_op_true))
        self.assertFalse(self.evaluator.evaluate(not_op_false))

    def testEvaluateOr(self):
        # or
        self.assertTrue(self.evaluator.evaluate(or_true))
        self.assertFalse(self.evaluator.evaluate(or_false))

    def testEvaluateXor(self):
        # xor
        self.assertTrue(self.evaluator.evaluate(xor_true))
        self.assertFalse(self.evaluator.evaluate(xor_false1))
        self.assertFalse(self.evaluator.evaluate(xor_false2))

    def testEvaluateXnor(self):
        # xnor
        self.assertTrue(self.evaluator.evaluate(xnor_true1))
        self.assertTrue(self.evaluator.evaluate(xnor_true2))
        self.assertFalse(self.evaluator.evaluate(xnor_false))

    def testEvaluateNor(self):
        # nor
        self.assertTrue(self.evaluator.evaluate(nor_true))
        self.assertFalse(self.evaluator.evaluate(nor_false1))
        self.assertFalse(self.evaluator.evaluate(nor_false2))

    def testEvaluateMembership(self):
        # in
        self.assertTrue(self.evaluator.evaluate(in_true))
        self.assertFalse(self.evaluator.evaluate(in_false))

    def testEvaluateNestedAnd(self):
        # nested and
        self.assertTrue(self.evaluator.evaluate(nested_and_true))
        self.assertFalse(self.evaluator.evaluate(nested_and_false))

    def testEvaluateNestedAndOr(self):
        # nested and or
        self.assertTrue(self.evaluator.evaluate(nested_and_or_true))
        self.assertFalse(self.evaluator.evaluate(nested_and_or_false))

    def testEvaluateAllTrue(self):
        self.assertTrue(self.evaluator.evaluate_all([and_true, not_op_true, nested_and_or_true]))

    def testEvaluateAllFalse(self):
        self.assertFalse(self.evaluator.evaluate_all([and_true, not_op_true, nested_and_or_false]))

if __name__ == "__main__":
    unittest.main()



