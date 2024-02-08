import os, sys, json

from functools import partial
from typing import Dict

from owe_python_sdk.runtime.runtime import Runtime


class ExecutionContext:
    def __init__(self, runtime: Runtime):
        self._runtime = runtime
        self.output_dir = runtime.OUTPUT_DIR
        self.input_dir = runtime.INPUT_DIR
        self.exec_dir = runtime.EXEC_DIR
        self.input_schema = runtime.INPUT_SCHEMA
        self.input_ids = list(self.input_schema.keys())
        self._hook_active = False
        self._exit_hooks: Dict[int, partial] = {0: [],1: []}

    def add_hook(self, exit_code: int, hook: callable, *args, **kwargs):
        if type(exit_code) != int:
            raise TypeError("Error registering hook. Argument 'exit_code' must be an integer")
        
        if not callable(hook):
            raise TypeError("Error registering hook. Argument 'hook' must be callable")
        
        self._exit_hooks(exit_code, partial(hook, *args, **kwargs))

        return self
        

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

    def stderr(self, code: int, message, call_hooks=True):
        """Exits with error"""
        if code < 1:
            raise Exception("Exit code provided must be an int with a value >= 1")

        with open(self._runtime.STDERR, "w") as file:
            file.write(message)
        
        call_hooks and self._call_hooks(code)

        sys.exit(code)

    def stdout(self, value, call_hooks=True):
        """Exits the process with no error"""
        with open(self._runtime.STDOUT, "a") as file:
            if type(value) == dict:
                value = json.dumps(value)

            file.write(str(value))

        call_hooks and self._call_hooks(0)

        sys.exit(0)

    def _call_hooks(self, exit_code):
        """Enables users to trigger functionality when lifecycle methods such as
        .stdout and .stderr are called"""
        # Prevent hooks from being called recursively
        if self._hook_active:
            raise Exception("Recursive hook calls are not permitted. This happens when user-defined hooks call functions on the 'runtime.execution_context' object that trigger hooks. Try passing the 'call_hooks' keyword argument as false in you hook.")
        # Call each hook in the order that they were registered
        for hook in self._exit_hooks.get(exit_code, []):
            self._hook_active = True
            try:
                hook()
            except Exception as e:
                self.stderr(1, f"Error caught in hook: {str(e)}", call_hooks=False)
            self._hook_active = False

execution_context = ExecutionContext(Runtime())