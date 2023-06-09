STDOUT = ".stdout"
STDERR = ".stderr"
INPUT_PREFIX = "_OWE_WORKFLOW_INPUT_"

FUNCTION_TASK_RUNTIMES = {
    "python": [
        "python:latest",
        "python:slim",
        "python:3.12",
        "python:3.12-slim",
        "python:3.11",
        "python:3.11-slim",
        "python:3.10",
        "python:3.10-slim",
        "python:3.9",
        "python:3.9-slim",
        "python:3.8",
        "python:3.8-slim"
    ]
}

FUNCTION_TASK_INSTALLERS = {
    "python": [
        "pip"
    ]
}