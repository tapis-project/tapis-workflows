import os

import pika

from pika.exchange_type import ExchangeType


# Define on_message_callback
def on_message_callback(ch, method, properties, body):
    print(body)

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

# Declare the queue
queue = channel.queue_declare(queue="", exclusive=True)

# Bind the queue to the channel
channel.queue_bind(exchange="builds", queue=queue.method.queue)

# Start cosuming the queue
channel.basic_consume(queue=queue.method.queue, auto_ack=True,
    on_message_callback=on_message_callback)

channel.start_consuming()
