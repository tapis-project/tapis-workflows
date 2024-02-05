import numpy
from tapipy.tapis import Tapis

# Use the execution context to fetch input data, save data to outputs,
# and terminate the task with the stdout and stderr functions
from owe_python_sdk.runtime import execution_context as ctx


num1 = int(ctx.get_input("NUM1"))
num2 = int(ctx.get_input("NUM2"))
num3 = int(ctx.get_input("NUM3"))

ctx.set_output("sum123", num1 + num2 + num3)
ctx.set_output("text.txt", "This is some text")

ctx.stdout("Hello from stdout")
