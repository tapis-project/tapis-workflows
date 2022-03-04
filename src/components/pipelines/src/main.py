import os, sys, time

from json.decoder import JSONDecodeError

import pika

from pika.exchange_type import ExchangeType

from core.PipelineService import pipeline_service as service
from conf.configs import MAX_CONNECTION_ATTEMPTS, RETRY_DELAY
from utils.bytes_to_json import bytes_to_json
from utils.json_to_object import json_to_object


# Resolve the image builder 
def on_message_callback(ch, method, properties, body):
    try:
        pipeline_context = json_to_object(bytes_to_json(body))
    except JSONDecodeError as e:
        # TODO reject the message if the body is not valid json
        return

    # try:
    service.start(pipeline_context)
    # except Exception as e:
    #     print(e)

# Initialize connection parameters
credentials = pika.PlainCredentials(os.environ["BROKER_USER"], os.environ["BROKER_PASSWORD"])
connection_parameters = pika.ConnectionParameters(
    os.environ["BROKER_URL"],
    os.environ["BROKER_PORT"],
    "/",
    credentials,
    heartbeat=0
)

# Attempt to connect to the message broker
connected = False
connection_attempts = 0
print("Starting connection with message broker...")
while connected == False and connection_attempts <= MAX_CONNECTION_ATTEMPTS:
    try:
        connection_attempts = connection_attempts + 1
        connection = pika.BlockingConnection(connection_parameters)
        connected = True
    except Exception:
        print(f"Attempting to connect to message broker... Attempts({connection_attempts})")
        time.sleep(RETRY_DELAY)

# Kill the build service if unable to connect
if connected == False:
    print(f"Error: Maximum connection attempts reached({MAX_CONNECTION_ATTEMPTS}). Unable to connect to message broker.")
    sys.exit(1)

print("Successfully connected to message broker")

# Create a channel and declare an exchange
channel = connection.channel()
channel.exchange_declare("pipelines", exchange_type=ExchangeType.fanout)

# Declare the queue
queue = channel.queue_declare(queue="", exclusive=True)

# Bind the queue to the channel
channel.queue_bind(exchange="pipelines", queue=queue.method.queue)

# Start cosuming the queue
channel.basic_consume(queue=queue.method.queue, auto_ack=True,
    on_message_callback=on_message_callback)

channel.start_consuming()
