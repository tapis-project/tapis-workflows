#!/bin/bash

# make the log file dir and file if it does not exist
mkdir -p logs
touch logs/workflows.logs

python setup.py
python main.py