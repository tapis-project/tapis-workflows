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
        
    def testCompare(self):
        # comparison
        self.assertTrue(self.evaluator.evaluate(comparison_true))
        self.assertFalse(self.evaluator.evaluate(comparison_false))

    def testAnd(self):
        # and
        self.assertTrue(self.evaluator.evaluate(and_true))
        self.assertFalse(self.evaluator.evaluate(and_false))

    def testNot(self):
        # not
        self.assertTrue(self.evaluator.evaluate(not_op_true))
        self.assertFalse(self.evaluator.evaluate(not_op_false))

    def testOr(self):
        # or
        self.assertTrue(self.evaluator.evaluate(or_true))
        self.assertFalse(self.evaluator.evaluate(or_false))

    def testXor(self):
        # xor
        self.assertTrue(self.evaluator.evaluate(xor_true))
        self.assertFalse(self.evaluator.evaluate(xor_false1))
        self.assertFalse(self.evaluator.evaluate(xor_false2))

    def testXnor(self):
        # xnor
        self.assertTrue(self.evaluator.evaluate(xnor_true1))
        self.assertTrue(self.evaluator.evaluate(xnor_true2))
        self.assertFalse(self.evaluator.evaluate(xnor_false))

    def testNor(self):
        # nor
        self.assertTrue(self.evaluator.evaluate(nor_true))
        self.assertFalse(self.evaluator.evaluate(nor_false1))
        self.assertFalse(self.evaluator.evaluate(nor_false2))

    def testMembership(self):
        # in
        self.assertTrue(self.evaluator.evaluate(in_true))
        self.assertFalse(self.evaluator.evaluate(in_false))

    def testNestedAnd(self):
        # nested and
        self.assertTrue(self.evaluator.evaluate(nested_and_true))
        self.assertFalse(self.evaluator.evaluate(nested_and_false))

    def testNestedAndOr(self):
        # nested and or
        self.assertTrue(self.evaluator.evaluate(nested_and_or_true))
        self.assertFalse(self.evaluator.evaluate(nested_and_or_false))

if __name__ == "__main__":
    unittest.main()



