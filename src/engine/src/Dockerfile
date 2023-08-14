FROM python:3.9

# Kubernetes binary
RUN cd /usr/bin; curl -LO https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl
RUN chmod 755 /usr/bin/kubectl

RUN apt-get update

RUN apt-get install -y vim git

RUN mkdir src
RUN mkdir /var/lib/open-workflow-engine/.config

COPY src/engine/src/requirements.txt /src/requirements.txt

WORKDIR /src

RUN pip install -r requirements.txt

COPY src/engine/src /src

# Tapisservice config and configschema
COPY src/shared/conf/config.json /src/config.json
COPY src/shared/conf/configschema.json /src/configschema.json

# Shared utils and helpers
COPY src/shared/GraphValidator.py /src/helpers
COPY src/shared/TapisServiceAPIGateway.py /src/contrib/tapis/helpers
COPY src/shared/OWESpec.yaml /var/lib/open-workflow-engine

RUN chmod +x /src/scripts/start.sh