FROM python:3.9

RUN mkdir src

COPY . /src

WORKDIR /src

RUN pip install -r requirements.txt

# ENV API_PORT=8000
# EXPOSE ${API_PORT}

# RUN chmod +x ./scripts/run.sh
# ENTRYPOINT [ "./scripts/run.sh" ]