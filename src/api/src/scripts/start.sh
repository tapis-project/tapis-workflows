#!/bin/bash

chmod a+x ./scripts/init.sh
./scripts/init.sh
uwsgi --http 0.0.0.0:8000 --module workflows.wsgi:application --master --die-on-term --logto /dev/stdout
# uvicorn workflows.asgi:application --host 0.0.0.0 --port 8000
# gunicorn --bind 0.0.0.0:8000 --workers 3 workflows.wsgi --worker-class gevent --timeout 600
# python3 manage.py runserver 0.0.0.0:8000;