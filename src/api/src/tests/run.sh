cd $(dirname $0)
cd ../

python3 -m unittest -v tests.TestUrls
python3 -m unittest -v tests.TestImports
python3 -m unittest -v tests.TestTapisETLPipeline