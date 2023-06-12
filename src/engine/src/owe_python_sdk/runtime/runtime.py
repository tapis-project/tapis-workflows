import os

from owe_python_sdk.constants import STDOUT, STDERR


class Runtime:
    def __init__(self):
        self.OUTPUT_DIR = os.environ.get("OWE_OUTPUT_DIR")
        self.EXEC_DIR = os.environ.get("OWE_EXEC_DIR")
        self.STDOUT = os.path.join(self.OUTPUT_DIR, STDOUT)
        self.STDERR = os.path.join(self.OUTPUT_DIR, STDERR)