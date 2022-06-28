#!/bin/bash

# Create the tapisservice config and config schema
python backend/setup.py

# Migrates the db schema
chmod a+x ./scripts/migrate.sh
./scripts/migrate.sh

# Uses the envrionment variables to resolve superuser username,
# password, and email
python3 manage.py createsuperuser --no-input || true;