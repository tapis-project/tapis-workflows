cd $(dirname $0)
cd ../
# TODO return with non-zero exit code if a test fails
# python3 -m unittest -v tests.TestServer

python3 -m unittest -v tests.TestConditionalExpressionEvaluator
python3 -m unittest -v tests.TestIOCContainerFactory
python3 -m unittest -v tests.TestTaskRepository
python3 -m unittest -v tests.TestSDKUtils