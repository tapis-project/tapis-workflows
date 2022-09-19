
import os, sys, time, asyncio, logging, threading

from typing import Literal, Union
from functools import partial
from json.decoder import JSONDecodeError


import pika

from pika.exceptions import AMQPError
from pika.exchange_type import ExchangeType

from conf.configs import (
    MAX_CONNECTION_ATTEMPTS,
    STARTING_WORKERS,
    MAX_WORKERS,
    RETRY_DELAY,
    WORKFLOWS_EXCHANGE,
)

from core.WorkflowExecutor import WorkflowExecutor
from core.WorkerPool import WorkerPool
from utils import bytes_to_json, json_to_object, lbuffer_str as lbuf


SSTR = lbuf("[SYSTEM]")

class Application:
    def __init__(self):
        # Attempt to connect to the message broker
        logging.info(f"{SSTR} Workflow Executor [STARTING]")
        
        # The pipelines that are currently running.
        self.running_pipelines = []

        # Create a worker pool that consists of the workflow executors that will
        # run the pipelines
        self.executors = WorkerPool(
            worker_cls=WorkflowExecutor,
            starting_worker_count=STARTING_WORKERS,
            max_workers=MAX_WORKERS,
        )

        logging.info(f"{SSTR} Workflow Executor [INITIALIZING WORKERS] ({self.executors.count()})")

    def __call__(self):
        # Connect to the message broker
        connection = self._connect()

        # Consume the messages on the workflows exchange.
        # Create a channel and declare an exchange
        channel = connection.channel()
        channel.exchange_declare(WORKFLOWS_EXCHANGE, exchange_type=ExchangeType.fanout)

        # Declare the queue
        queue = channel.queue_declare(queue="", exclusive=True)

        # Bind the queue to the channel
        channel.queue_bind(exchange=WORKFLOWS_EXCHANGE, queue=queue.method.queue)

        # Start cosuming
        threads = []

        try:
            channel.basic_consume(
                queue=queue.method.queue,
                auto_ack=False,
                on_message_callback=partial(
                    self._on_message_callback,
                    args=(connection, threads)
                )
            )

            channel.start_consuming()

            logging.info(f"{SSTR} READY")

            # Wait for all to complete
            for thread in threads:
                thread.join()

            connection.close()

        # Occurs when basic consume recieveds the wrong args
        except ValueError as e:
            logging.critical(f"Critical Workflow Executor Error: {e}")
        # Cathes all ampq errors from .start_consuming()
        except AMQPError as e:
            logging.error(e)
        # Catch all other exceptions
        except Exception as e:
            logging.error(e)


    def _run(self, ctx, connection, channel, delivery_tag):
        # NOTE Currently acking after the workflow executor runs.
        acked = False
        try:
            # Get the pipeline executor
            executor = self.executors.check_out()
            if executor != None:
                # Ack the message before running the workflow executor
                cb = partial(self._ack_nack, "ack", channel, delivery_tag)
                connection.add_callback_threadsafe(cb)
                
                # Set the acked flag
                acked = True

                # Run the workflow executor
                asyncio.run(executor.run(ctx))

        except Exception as e:
            logging.error(e)

            # Nack the message if it has not already been ack
            if not acked:
                cb = partial(self._ack_nack, "nack", channel, delivery_tag)
                connection.add_callback_threadsafe(cb)

        # Return the pipeline executor back to the worker pool
        self.executors.check_in(executor)

    def _on_message_callback(self, channel, method, _, body, args):
        # Prepare the message
        try:
            ctx = json_to_object(bytes_to_json(body))
        except JSONDecodeError as e:
            logging.error(e)
            channel.basic_reject(method.delivery_tag, requeue=False)
            return

        # # Register the running pipeline
        # self.running_pipelines.append(message.pipeline)
        
        (connection, threads) = args
        t = threading.Thread(
            target=self._run,
            args=(ctx, connection, channel, method.delivery_tag)
        )
        t.start()
        threads.append(t)

    def _ack_nack(
        self,
        ack_nack: Union[Literal["ack"], Literal["nack"]],
        channel,
        delivery_tag
    ):
        fn = channel.basic_ack if ack_nack == "ack" else channel.basic_nack
        if channel.is_open:
            fn(delivery_tag)
            return
        
        # TODO do something if channel is closed

    def _pipeline_in_progress(self, pipeline):
        return False

    def _connect(self):
        # Initialize connection parameters with plain credentials
        connection_parameters = pika.ConnectionParameters(
            os.environ["BROKER_URL"],
            os.environ["BROKER_PORT"],
            "/",
            pika.PlainCredentials(
                os.environ["BROKER_USER"], os.environ["BROKER_PASSWORD"])
        )

        logging.info(f"{SSTR} Workflow Executor [CONNECTING]")

        connected = False
        connection_attempts = 0
        while connected == False and connection_attempts <= MAX_CONNECTION_ATTEMPTS:
            try:
                connection_attempts = connection_attempts + 1
                connection = pika.BlockingConnection(connection_parameters)
                connected = True
            except Exception:
                logging.info(f"{SSTR} Workflow Executor [CONNECTION FAILED] ({connection_attempts})")
                time.sleep(RETRY_DELAY)

        # Kill the build service if unable to connect
        if connected == False:
            logging.critical(
                f"\nError: Maximum connection attempts reached({MAX_CONNECTION_ATTEMPTS}). Unable to connect to message broker."
            )
            sys.exit(1)

        logging.info(f"{SSTR} Workflow Executor [CONNECTED]")

        return connection


    
