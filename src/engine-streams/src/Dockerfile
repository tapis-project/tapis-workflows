FROM node:16.7

RUN apt-get update

RUN apt-get install -y vim git

RUN mkdir src

COPY ./src/engine-streams/src/package.json /src/package.json

WORKDIR /src

RUN npm install

COPY src/engine-streams/src /src

RUN npm run build

ENTRYPOINT [ "npm", "run", "deploy" ]