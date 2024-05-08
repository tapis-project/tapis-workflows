STDOUT = ".stdout"
STDERR = ".stderr"
LOGFILE = ".logs"
INPUT_PREFIX = "_OWE_WORKFLOW_INPUT_"

FUNCTION_TASK_RUNTIMES = {
    "linux": [
        "ubuntu:latest",
        "ubuntu:23:10"
    ],
    "python": [
        # Basic python
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

        # Machine Learning
        "tensorflow/tensorflow:latest",
        "tensorflow/tensorflow:latest-gpu",
        "tensorflow/tensorflow:2.12.0",
        "tensorflow/tensorflow:2.12.0-gpu",
        "pytorch/pytorch:latest",
        "huggingface/transformers-pytorch-gpu:latest",
        "huggingface/transformers-pytorch-gpu:4.29.2"
    ]
}

FUNCTION_TASK_INSTALLERS = {
    "linux": [
        "apt-get"
    ],
    "python": [
        "pip"
    ],
}