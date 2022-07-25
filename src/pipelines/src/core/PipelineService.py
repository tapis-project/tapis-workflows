
import os, sys, time, asyncio, logging

from json.decoder import JSONDecodeError

import pika

from pika.exchange_type import ExchangeType

from conf.configs import (
    MAX_CONNECTION_ATTEMPTS,
    STARTING_WORKERS,
    MAX_WORKERS,
    RETRY_DELAY
)
from utils.bytes_to_json import bytes_to_json
from utils.json_to_object import json_to_object

from core.PipelineExecutor import PipelineExecutor
from core.WorkerPool import WorkerPool

# TODO NOTE pipelines cannot run at the same time with this setup
class PipelineService:
    def __init__(self):
        # Create a worker pool that consists of the pipeline executors that will
        # run the pipelines
        self.worker_pool = WorkerPool(
            worker_cls=PipelineExecutor,
            starting_worker_count=STARTING_WORKERS,
            max_workers=MAX_WORKERS
        )

    def start(self):
        # Initialize connection parameters with plain credentials
        connection_parameters = pika.ConnectionParameters(
            os.environ["BROKER_URL"],
            os.environ["BROKER_PORT"],
            "/",
            pika.PlainCredentials(
                os.environ["BROKER_USER"], os.environ["BROKER_PASSWORD"])
        )

        # Attempt to connect to the message broker
        logging.info("Starting connection with message broker...")

        connected = False
        connection_attempts = 0
        while connected == False and connection_attempts <= MAX_CONNECTION_ATTEMPTS:
            try:
                connection_attempts = connection_attempts + 1
                connection = pika.BlockingConnection(connection_parameters)
                connected = True
            except Exception:
                logging.info(
                    f"Attempting to connect to message broker... Attempts({connection_attempts})"
                )
                time.sleep(RETRY_DELAY)

        # Kill the build service if unable to connect
        if connected == False:
            logging.critical(
                f"Error: Maximum connection attempts reached({MAX_CONNECTION_ATTEMPTS}). Unable to connect to message broker."
            )
            sys.exit(1)

        logging.info("Successfully connected to message broker")

        # Consume the messages on the workflows exchange
        # Create a channel and declare an exchange
        channel = connection.channel()
        channel.exchange_declare("workflows", exchange_type=ExchangeType.fanout)

        # Declare the queue
        queue = channel.queue_declare(queue="", exclusive=True)

        # Bind the queue to the channel
        channel.queue_bind(exchange="workflows", queue=queue.method.queue)

        # Start cosuming the queue
        channel.basic_consume(
            queue=queue.method.queue,
            auto_ack=False,
            on_message_callback=self._on_message_callback
        )

        channel.start_consuming()

    def _work(self):
        pass

    # Resolve the image builder
    def _on_message_callback(self, channel, method, properties, body):
        logging.debug("Message recieved")
        try:
            # Decode the message
            message = json_to_object(bytes_to_json(body))

            # Get the pipeline executor
            executor = self.worker_pool.get()
            if executor != None:
                asyncio.run(executor.start(message))

                # Return the pipeline executor back to the 
                self.worker_pool.join(executor)
                self._ack_message(channel, method.delivery_tag)

        except JSONDecodeError as e:
            logging.error(e)
            # TODO reject the message
            return
        except Exception as e:
            logging.error(e.__class__.__name__, e)
            return

    def _ack_message(self, channel, delivery_tag):
        if channel.is_open:
            channel.basic_ack(delivery_tag)
            return
        
        # TODO do something if channel is closed


    
