import os, sys, json

from owe_python_sdk.runtime.runtime import Runtime
from owe_python_sdk.constants import INPUT_PREFIX


class ExecutionContext:
    def __init__(self, runtime: Runtime):
        self._runtime = runtime
        self.output_dir = runtime.OUTPUT_DIR
        self.input_dir = runtime.INPUT_DIR
        self.exec_dir = runtime.EXEC_DIR
        self.input_schema = runtime.INPUT_SCHEMA
        self.input_ids = list(self.input_schema.keys())

    def get_input(self, input_id, default=None):
        contents = None
        try:
            with open(os.path.join(self.input_dir, input_id), mode="r") as file:
                contents = file.read()
        except FileNotFoundError:
            return default

        if contents == "": return None

        return contents
    
    def find_inputs(self, contains=None):
        if contains == None: return self.input_ids
        ids = [input_id for input_id in self.input_ids if contains in input_id]
        return ids

    def set_output(self, _id, value, encoding=None):
        flag = "wb"
        # If no encoding specified, save the value as text
        if encoding == None:
            flag = "w"
            value = str(value)

        with open(os.path.join(self.output_dir, _id), flag, encoding=encoding) as file:
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