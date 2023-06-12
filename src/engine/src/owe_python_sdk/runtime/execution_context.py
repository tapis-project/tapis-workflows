import os, sys, json

from owe_python_sdk.runtime.runtime import Runtime
from owe_python_sdk.constants import INPUT_PREFIX


class ExecutionContext:
    def __init__(self, runtime: Runtime):
        self._runtime = runtime
        self.output_dir = runtime.OUTPUT_DIR
        self.exec_dir = runtime.EXEC_DIR

    def get_input(self, key, default=None):
        input_var = os.environ.get(INPUT_PREFIX + key, default=default)

        return input_var

    def set_output(self, _id, value, encoding=None):
        flag = "wb"
        # If no encoding specified, save the value as text
        if encoding == None:
            flag = "w"
            value = str(value)

        with open(os.path.join(self._runtime.output_dir, _id), flag, encoding=encoding) as file:
            file.write(value)

    def stderr(self, code: int, message):
        if code < 1:
            raise Exception("Exit code provided must be an int with a value >= 1")

        with open(self._runtime.STDERR, "w") as file:
            file.write(message)

        sys.exit(code)

    def stdout(self, value):
        with open(self._runtime.STDOUT, "w") as file:
            if type(value) == dict:
                value = json.dumps(value)

            file.write(str(value))

        sys.exit(0)

execution_context = ExecutionContext(Runtime())