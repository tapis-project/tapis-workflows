import os, json

from owe_python_sdk.constants import STDOUT, STDERR


class Runtime:
    def __init__(self):
        self.INPUT_DIR = os.environ.get("_OWE_INPUT_DIR")
        self.OUTPUT_DIR = os.environ.get("_OWE_OUTPUT_DIR")
        self.EXEC_DIR = os.environ.get("_OWE_EXEC_DIR")
        self.PIPELINE_ID = os.environ.get("_OWE_PIPELINE_ID")
        self.PIPELINE_RUN_UUID = os.environ.get("_OWE_PIPELINE_RUN_UUID")
        self.TASK_ID = os.environ.get("_OWE_TASK_ID")
        self.STDOUT = os.path.join(self.OUTPUT_DIR, STDOUT)
        self.STDERR = os.path.join(self.OUTPUT_DIR, STDERR)
        self.INPUT_SCHEMA = json.loads(os.environ.get("_OWE_INPUT_SCHEMA"))