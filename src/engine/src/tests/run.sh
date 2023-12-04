cd $(dirname $0)
cd ../
python3 -m unittest -v tests.TestServer
python3 -m unittest -v tests.TestConditionalExpressionEvaluator
python3 -m unittest -v tests.TestIOCContainerFactory
python3 -m unittest -v tests.TestTaskRepository