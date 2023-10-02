FROM python:3.9-slim

RUN apt-get clean

RUN apt-get update

RUN apt-get install -y vim

RUN mkdir src

COPY src/api/src/requirements.txt /src/requirements.txt

WORKDIR /src

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY src/api/src/ /src

# Shared utils and helpers
COPY src/shared/GraphValidator.py /src/backend/helpers
COPY src/shared/TapisServiceAPIGateway.py /src/backend/services
COPY src/shared/OWESpec.yaml /src/conf

# Tapisservice config and configschema
COPY src/shared/conf/ /src/backend


