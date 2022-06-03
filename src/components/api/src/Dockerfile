FROM python:3.9

RUN apt-get update

RUN apt-get install -y vim

RUN mkdir src

COPY . /src

WORKDIR /src

RUN pip install -r requirements.txt