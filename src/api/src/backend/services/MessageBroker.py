import os

import pika

from pika.exchange_type import ExchangeType

from backend.errors.message_broker import InvalidExchangeError


EXCHANGES = [
    "workflows",
    "tasks",
]

class MessageBroker:
    def __init__(self):
        self.user = os.environ["BROKER_USER"]
        self.password = os.environ["BROKER_PASSWORD"]
        self.url = os.environ["BROKER_URL"]
        self.port = os.environ["BROKER_PORT"]
        self.channel = None

        self.connection_parameters = pika.ConnectionParameters(
            self.url,
            self.port,
            "/",
            pika.PlainCredentials(self.user, self.password)
        )


    def _open_connection(self):
        # Initialize connection to the message queue
        self.connection = pika.BlockingConnection(self.connection_parameters)

        # Create a channel and declare an exchange
        self.channel = self.connection.channel()

    def _close_connection(self):
        self.connection.close()

    def _validate_exchange(self, exchange):
        # Normalize the exchange name
        if exchange not in EXCHANGES:
            raise InvalidExchangeError(f"Exchange {exchange} is not a valid option. Exchanges: {EXCHANGES}")

    def publish(self, exchange, message):
        self._validate_exchange(exchange)
        self._open_connection()
        self.channel.exchange_declare(exchange, exchange_type=ExchangeType.fanout)

        # Publish message to the message queue and close the connection
        self.channel.basic_publish(exchange=exchange, routing_key="", body=message)
        self._close_connection()

service = MessageBroker()