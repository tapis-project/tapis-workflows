#!/bin/bash

python3 manage.py createsuperuser --no-input || true;
python3 manage.py makemigrations;
python3 manage.py migrate;