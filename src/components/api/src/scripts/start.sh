#!/bin/bash

chmod a+x ./scripts/init.sh
./scripts/init.sh
python3 manage.py runserver 0.0.0.0:8000;