import os

from owe_python_sdk.constants import STDOUT, STDERR


class Runtime:
    def __init__(self):
        self.output_dir = os.environ.get("OWE_OUTPUT_DIR")
        self.exec_dir = os.environ.get("OWE_EXEC_DIR")
        self.stdout = os.path.join(self.output_dir, STDOUT)
        self.stderr = os.path.join(self.output_dir, STDERR)