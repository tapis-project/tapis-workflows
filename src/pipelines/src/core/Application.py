
import os, sys, time, asyncio, logging, threading

from json.decoder import JSONDecodeError
from functools import partial

import pika

from pika.exchange_type import ExchangeType

from conf.configs import (
    MAX_CONNECTION_ATTEMPTS,
    STARTING_WORKERS,
    MAX_WORKERS,
    RETRY_DELAY,
    WORKFLOWS_EXCHANGE,
)
from utils.bytes_to_json import bytes_to_json
from utils.json_to_object import json_to_object
from utils import lbuffer_str as lbuf

from core.PipelineExecutor import PipelineExecutor
from core.WorkerPool import WorkerPool


SSTR = lbuf("[SYSTEM]")

class Application:
    def __init__(self):
        # Attempt to connect to the message broker
        logging.info(f"{SSTR} STARTING PIPELINE SERVICE")
        
        # The pipelines that are currently running.
        self.running_pipelines = []

        # Create a worker pool that consists of the pipeline executors that will
        # run the pipelines
        self.executors = WorkerPool(
            worker_cls=PipelineExecutor,
            starting_worker_count=STARTING_WORKERS,
            max_workers=MAX_WORKERS,
        )

        logging.info(f"{SSTR} INITIALIZING WORKERS ({self.executors.count()})")

    def __call__(self):
        # Initialize connection parameters with plain credentials
        connection_parameters = pika.ConnectionParameters(
            os.environ["BROKER_URL"],
            os.environ["BROKER_PORT"],
            "/",
            pika.PlainCredentials(
                os.environ["BROKER_USER"], os.environ["BROKER_PASSWORD"])
        )

        logging.info(f"{SSTR} CONNECTING TO BROKER")

        connected = False
        connection_attempts = 0
        while connected == False and connection_attempts <= MAX_CONNECTION_ATTEMPTS:
            try:
                connection_attempts = connection_attempts + 1
                connection = pika.BlockingConnection(connection_parameters)
                connected = True
            except Exception:
                logging.info(f"{SSTR} FAILED CONNECTON ({connection_attempts})")
                time.sleep(RETRY_DELAY)

        # Kill the build service if unable to connect
        if connected == False:
            logging.critical(
                f"\nError: Maximum connection attempts reached({MAX_CONNECTION_ATTEMPTS}). Unable to connect to message broker."
            )
            sys.exit(1)

        logging.info(f"{SSTR} CONNECTED")

        # Consume the messages on the workflows exchange
        # Create a channel and declare an exchange
        channel = connection.channel()
        channel.exchange_declare(WORKFLOWS_EXCHANGE, exchange_type=ExchangeType.fanout)

        # Declare the queue
        queue = channel.queue_declare(queue="", exclusive=True)

        # Bind the queue to the channel
        channel.queue_bind(exchange=WORKFLOWS_EXCHANGE, queue=queue.method.queue)

        # Start cosuming
        threads = []

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

    def _run(self, message, connection, channel, delivery_tag):
        try:
            # Get the pipeline executor
            executor = self.executors.check_out()
            if executor != None:
                asyncio.run(executor.start(message))

                # Return the pipeline executor back to the worker pool
                self.executors.check_in(executor)
        except Exception as e:
            logging.error(e.__class__.__name__, e)
            # TODO nack or ack?
            return

        cb = partial(self._ack_message, channel, delivery_tag)
        connection.add_callback_threadsafe(cb)

    def _on_message_callback(self, channel, method, _, body, args):
        # Prepare the message
        try:
            message = json_to_object(bytes_to_json(body))
        except JSONDecodeError as e:
            logging.error(e)
            channel.basic_reject(method.delivery_tag, requeue=False)
            return

        # # TODO If incoming message is for a pipeline that is currently
        # # running, terminate the running pipeline
        # if (
        #     message.pipeline.exclusive
        #     and self._pipeline_in_progress(message.pipeline)
        # ):
        #     executor = filter(
        #         lambda executor: (
        #             executor.pipeline.id == message.pipeline.id
        #             and self.message.group.id == "<something_here>"
        #             and self.message.group.tenant_id == "<something_here>"
        #         ),
        #         self.executors.get_all_running()
        #     )

        #     executor.terminate()

        # # Register the running pipeline
        # self.running_pipelines.append(message.pipeline)
        
        (connection, threads) = args
        t = threading.Thread(
            target=self._run,
            args=(message, connection, channel, method.delivery_tag)
        )
        t.start()
        threads.append(t)

    def _ack_message(self, channel, delivery_tag):
        if channel.is_open:
            channel.basic_ack(delivery_tag)
            return
        
        # TODO do something if channel is closed

    def _pipeline_in_progress(self, pipeline):
        return False


    
