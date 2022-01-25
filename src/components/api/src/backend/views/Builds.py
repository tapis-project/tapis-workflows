import json, os

import pika

from django.http import HttpResponse
from django.views import View
from pika.exchange_type import ExchangeType

# TODO Remove
from backend.fixtures.build_context import build_context
from backend.helpers.parse_commit import parse_commit as parse


class Builds(View):

    def get(self, request):
        # TODO Remove: Testing build
        return self.post(request)
    
    def post(self, request):
        # Fetch the build context that matches incoming request
        # TODO fetch build context data
        directives = parse(build_context["event"]["commit"])
        build_context["directives"] = directives
        message = json.dumps(build_context)

        # Initialize connection to the message queue
        credentials = pika.PlainCredentials(os.environ["BROKER_USER"], os.environ["BROKER_PASSWORD"])
        connection_parameters = pika.ConnectionParameters(
            os.environ["BROKER_URL"],
            os.environ["BROKER_PORT"],
            "/",
            credentials
        )
        connection = pika.BlockingConnection(connection_parameters)

        # Create a channel and declare an exchange
        channel = connection.channel()
        channel.exchange_declare("builds", exchange_type=ExchangeType.fanout)

        # Publish message to the message queue and close the connection
        channel.basic_publish(exchange="builds", routing_key="", body=message)
        connection.close()

        # Create the build object with status QUEUED
        # TODO create build object

        # Respond with the build_context and build data
        return HttpResponse(f"Build data here: \n{directives}")

    def put(self, request):
        return HttpResponse(f"put")

    def patch(self, request):
        return HttpResponse(f"patch")

    def delete(self, request):
        return HttpResponse(f"delete")