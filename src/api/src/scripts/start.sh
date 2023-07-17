#!/bin/bash

chmod a+x ./scripts/init.sh
./scripts/init.sh
gunicorn --bind 0.0.0.0:8000 --workers 100 workflows.wsgi --worker-class gevent --timeout 600
# python3 manage.py runserver 0.0.0.0:8000;