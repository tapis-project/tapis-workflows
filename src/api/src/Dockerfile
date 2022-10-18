FROM python:3.9

RUN apt-get clean

RUN apt-get update

RUN apt-get install -y vim

RUN mkdir src

COPY src/api/src/requirements.txt /src/requirements.txt

WORKDIR /src

RUN pip install -r requirements.txt

COPY src/api/src/ /src

# Tapisservice config and configschema
COPY src/shared/conf/config.json /src/backend/config.json
COPY src/shared/conf/configschema.json /src/backend/configschema.json

# Shared utils and helpers
COPY src/shared/GraphValidator.py /src/backend/helpers/GraphValidator.py
COPY src/shared/TapisServiceAPIGateway.py /src/backend/services/TapisServiceAPIGateway.py

