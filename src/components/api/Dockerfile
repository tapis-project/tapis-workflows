FROM python:3.9

RUN mkdir cicd

COPY . /cicd

WORKDIR /cicd

RUN pip install -r requirements.txt

ENV API_PORT=3000
EXPOSE ${API_PORT}

RUN chmod +x ./scripts/run
ENTRYPOINT [ "./scripts/run" ]