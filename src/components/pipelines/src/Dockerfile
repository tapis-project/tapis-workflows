FROM python:3.9

# Kubernetes binary
RUN cd /usr/bin; curl -LO https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl
RUN chmod 755 /usr/bin/kubectl

RUN mkdir cicd

COPY . /cicd

WORKDIR /cicd

RUN pip install -r requirements.txt