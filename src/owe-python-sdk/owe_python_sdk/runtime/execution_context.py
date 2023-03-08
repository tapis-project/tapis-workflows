import os, sys

from owe_python_sdk.runtime.runtime import Runtime


class ExecutionContext:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    def set_output(self, _id, value):
        with open(os.path.join(self.runtime.output_dir, _id), "w") as file:
            file.write(value)

    def stderr(self, code, message):
        with open(self.runtime.stderr, "w") as file:
            file.write(message)

        sys.exit(code)

    def stdout(self, value):
        with open(self.runtime.stdout, "w") as file:
            file.write(value)

        sys.exit(0)

execution_context = ExecutionContext(Runtime())