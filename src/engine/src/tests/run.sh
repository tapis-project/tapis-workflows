cd $(dirname $0)
cd ../
python3 -m unittest tests.testserver
python3 -m unittest tests.TestConditionalExpressionEvaluator