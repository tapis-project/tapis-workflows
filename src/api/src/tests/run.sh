cd $(dirname $0)
cd ../

export DJANGO_SETTINGS_MODULE=workflows.settings_test
export ENV=LOCAL

python3 -m unittest -v tests.TestUrls
python3 -m unittest -v tests.TestImports
python3 -m unittest -v tests.TestTapisETLPipeline

# Tests that require django models must be tested through the testing utilities
# provided by django
# python3 manage.py test tests.TestModelSerializers