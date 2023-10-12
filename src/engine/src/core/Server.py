
import os, sys, time, logging, json
from threading import Thread

from typing import Literal, Union
from functools import partial
from json.decoder import JSONDecodeError


import pika

from pika.exceptions import AMQPError
from pika.exchange_type import ExchangeType

from conf.constants import (
    MAX_CONNECTION_ATTEMPTS,
    STARTING_WORKERS,
    MAX_WORKERS,
    CONNECTION_RETRY_DELAY,
    INSUFFICIENT_WORKER_RETRY_DELAY,
    INBOUND_EXCHANGE,
    RETRY_EXCHANGE,
    DEAD_LETTER_EXCHANGE,
    DEFERRED_EXCHANGE,
    INBOUND_QUEUE,
    RETRY_QUEUE,
    DEAD_LETTER_QUEUE,
    DEFERRED_QUEUE,
    DUPLICATE_SUBMISSION_POLICY_TERMINATE,
    DUPLICATE_SUBMISSION_POLICY_DENY,
    DUPLICATE_SUBMISSION_POLICY_ALLOW,
    DUPLICATE_SUBMISSION_POLICY_DEFER,
    PLUGINS,
)
from owe_python_sdk.schema import WorkflowSubmissionRequest, EmptyObject

from core.workers import WorkerPool
from core.workflows.executors import WorkflowExecutor
from utils import bytes_to_json, load_plugins, lbuffer_str as lbuf
from errors import NoAvailableWorkers, WorkflowTerminated

from pprint import pprint

logger = logging.getLogger("server")

# TODO Keep track of workflows submissions somehow so they can be terminated later
class Server:
    def __init__(self):
        self.active_workers = []
        self.worker_pool = None
        self.plugins = []

    def __call__(self):
        """Initializes the dynamic worker pool comprised of WorkflowExecutor
        workers, establishes a connection with RabbitMQ, creates the channel, 
        exchanges, and queues, and begins consuming from the inbound queue"""

        logger.info(f"{lbuf('[SERVER]')} STARTING")

        # Initialize plugins
        self.plugins = load_plugins(PLUGINS)

        # Create a worker pool that consists of the workflow executors that will
        # run the pipelines
        # TODO catch error for worker classes that dont inherit from "Worker"
        self.worker_pool = WorkerPool(
            worker_cls=WorkflowExecutor,
            starting_worker_count=STARTING_WORKERS,
            max_workers=MAX_WORKERS,
            worker_kwargs={
                "plugins": self.plugins
            }
        )
        logger.debug(f"{lbuf('[SERVER]')} WORKERS INITIALIZED ({self.worker_pool.count()})")

        # Connect to the message broker
        connection = self._connect()

        # Create the channel, exchanges, and queues
        channel = connection.channel()

        # Inbound exchange and queue handles workflow submissions or resubmissions
        channel.exchange_declare(INBOUND_EXCHANGE, exchange_type=ExchangeType.fanout)
        inbound_queue = channel.queue_declare(queue=INBOUND_QUEUE, exclusive=True)
        channel.queue_bind(exchange=INBOUND_EXCHANGE, queue=inbound_queue.method.queue)

        # TODO Future implementation
        # Deferred exchange and queue stores workflow submissions that await execution
        # of workflows with the same idempotency key
        channel.exchange_declare(DEFERRED_EXCHANGE, exchange_type=ExchangeType.fanout)
        deferred_queue = channel.queue_declare(queue=DEFERRED_QUEUE, exclusive=True)
        channel.queue_bind(exchange=DEFERRED_EXCHANGE, queue=deferred_queue.method.queue)
        
        # TODO Future Implementation
        # Retry exchange and queue is a temporary hold for messages that havent been
        # processed yet in the event that there are no workers available, or the workflow
        # executor has an ApplicationError
        channel.exchange_declare(RETRY_EXCHANGE, exchange_type=ExchangeType.fanout)
        retry_queue = channel.queue_declare(queue=RETRY_QUEUE)
        channel.queue_bind(exchange=RETRY_EXCHANGE, queue=retry_queue.method.queue)
        
        # TODO Future Implementation
        # Messages that are retried too many times get sent to the deadletter exchange
        # for inspection
        channel.exchange_declare(DEAD_LETTER_EXCHANGE, exchange_type=ExchangeType.fanout)
        dead_letter_queue = channel.queue_declare(queue=DEAD_LETTER_QUEUE)
        channel.queue_bind(exchange=DEAD_LETTER_EXCHANGE, queue=dead_letter_queue.method.queue)

        # The threads that will be started within the on_message callback
        threads = []

        # Start consuming the inbound queue
        try:
            channel.basic_consume(
                queue=inbound_queue.method.queue,
                auto_ack=False,
                on_message_callback=partial(
                    self._on_message_callback,
                    args=(connection, threads)
                )
            )

            channel.start_consuming()

            # Wait for all to complete
            for thread in threads:
                thread.join()

            connection.close()

        # Occurs when basic_consume recieves the wrong args
        except ValueError as e:
            logger.critical(f"Critical Workflow Executor Error: {e}")

        # Cathes all ampq errors from .start_consuming()
        except AMQPError as e:
            logger.error(f"{e.__class__.__name__} - {e}")

        # Catch all other exceptions
        except Exception as e:
            logger.error(e)

    def _start_worker(self, body, connection, channel, delivery_tag):
        """Validates and prepares the message from the inbound exchange(and queue),
        provisions a worker from the worker pool, acks the message, registers the 
        active worker to the server, handles the termination of duplicate
        workflow submissions and starts the worker."""

        # Prepare the execution context. The execution context contains all the 
        # information required to run a workflow
        worker = None
        acked = False # Indicates that the message as been acked
        try:
            # Decode the message body, then convert to an object.
            json_request = json.loads(bytes_to_json(body))
            pprint(json_request)
            request = WorkflowSubmissionRequest(**json_request)
            
            # Get a workflow executor worker. If there are none available,
            # this will raise a "NoWorkersAvailabe" error which is handled
            # an the exception block below
            worker = self.worker_pool.check_out()

            # Run request middlewares over the workflow context
            # NOTE Request middlewares will very likely mutate the workflow context
            for plugin in self.plugins:
                request = plugin.dispatch("request", request)
            
            # Ack the message before running the workflow executor
            cb = partial(self._ack_nack, "ack", channel, delivery_tag)
            connection.add_callback_threadsafe(cb)

            # Set the acked flag to True(Used to nack the message if an exception
            # occurs above)
            acked = True

            # Register the active worker to the server. If worker cannot 
            # execute, check it back in.
            worker = self._register_worker(request, worker)

            threads = []
            
            if worker.can_start:
                worker.start(request, threads)

            for t in threads:
                t.join()

        # Thrown when decoding the message body. Reject the message
        except JSONDecodeError as e:
            logger.error(e)
            channel.basic_reject(delivery_tag, requeue=False)
            return

        except NoAvailableWorkers:
            logger.info(f"{lbuf('[SERVER]')} Insufficient workers available. RETRYING (10s)")
            connection.add_callback_threadsafe(
                partial(
                    self._ack_nack,
                    "nack",
                    channel,
                    delivery_tag,
                    delay=INSUFFICIENT_WORKER_RETRY_DELAY
                )
            )
            return

        # TODO probably not needed
        # except WorkflowTerminated as e:
        #     logger.info(f"{lbuf('[SERVER]')} {e}")
        #     worker.reset()

        except Exception as e:
            logger.error(e)

            # Nack the message if it has not already been ack
            # TODO Nack the message into a retry queue. 
            # Or reject? Why would it not be rejected?
            if not acked:
                cb = partial(self._ack_nack, "nack", channel, delivery_tag)
                connection.add_callback_threadsafe(cb)
            raise e

        # Deregister and return executor back to the worker pool
        self._deregister_worker(worker)
        self.worker_pool.check_in(worker)

    def _on_message_callback(self, channel, method, _, body, args):
        (connection, threads) = args

        t = Thread(
            target=self._start_worker,
            args=(body, connection, channel, method.delivery_tag)
        )

        t.start()
        threads.append(t)

        # Clean up the stopped threads
        threads = [t for t in threads if t.is_alive()]

    def _ack_nack(
        self,
        ack_nack: Union[Literal["ack"], Literal["nack"]],
        channel,
        delivery_tag,
        delay=0
    ):
        fn = channel.basic_ack if ack_nack == "ack" else channel.basic_nack
        kwargs = {}
        if ack_nack == "nack": kwargs = {"requeue": False}
        if channel.is_open:
            # Wait the delay if necessary
            delay == 0 or time.sleep(abs(delay))
            fn(delivery_tag, **kwargs)
            return
        
        # TODO do something if channel is closed

    def _connect(self):
        # Initialize connection parameters with plain credentials
        connection_parameters = pika.ConnectionParameters(
            os.environ["BROKER_URL"],
            os.environ["BROKER_PORT"],
            "/",
            pika.PlainCredentials(
                os.environ["BROKER_USER"], os.environ["BROKER_PASSWORD"])
        )

        logger.info(f"{lbuf('[SERVER]')} CONNECTING TO BROKER")

        connected = False
        connection_attempts = 0
        while connected == False and connection_attempts <= MAX_CONNECTION_ATTEMPTS:
            try:
                connection_attempts = connection_attempts + 1
                connection = pika.BlockingConnection(connection_parameters)
                connected = True
            except Exception:
                logger.info(f"{lbuf('[SERVER]')} [CONNECTION FAILED] ({connection_attempts})")
                time.sleep(CONNECTION_RETRY_DELAY)

        # Kill the build service if unable to connect
        if connected == False:
            logger.critical(
                f"\nError: Maximum connection attempts reached({MAX_CONNECTION_ATTEMPTS}). Unable to connect to message broker."
            )
            sys.exit(1)

        logger.info(f"{lbuf('[SERVER]')} CONNECTED")

        return connection

    # TODO handle for the case of multiple active workers with same
    # active worker key
    def _register_worker(self, request, worker):
        """Registers the worker to the Server. Handles duplicate workflow
        submissions"""
        # Returns a key based on user-defined idempotency key or pipeline
        # run uuid if no idempotency key is provided
        worker.key = self._resolve_idempotency_key(request)

        # Set the idempotency key on the context
        request.idempotency_key = worker.key

        # Check if there are workers running that have the same unique constraint key
        active_workers = self._get_active_workers(worker.key)
        policy = request.pipeline.execution_profile.duplicate_submission_policy

        if (
            policy == DUPLICATE_SUBMISSION_POLICY_DENY
            and len(active_workers) > 0
        ):
            return worker
        elif policy == DUPLICATE_SUBMISSION_POLICY_TERMINATE:
            for active_worker in active_workers:
                active_worker.terminate()
                self._deregister_worker(active_worker, terminated=True)
        elif policy == DUPLICATE_SUBMISSION_POLICY_DEFER:
            logger.info(f"{lbuf('[SERVER]')} Warning: Duplicate Submission Policy of 'DEFER' not implemented. Handling as 'ALLOW'")
            pass
        elif policy == DUPLICATE_SUBMISSION_POLICY_ALLOW:
            pass
        
        worker.can_start = True
        self.active_workers.append(worker)

        return worker

    def _deregister_worker(self, worker, terminated=False):
        worker.key = None
        self.active_workers = [ w for w in self.active_workers if w.id != worker.id ]
        worker.reset(terminated=terminated)

    def _get_active_workers(self, key):
        return [worker for worker in self.active_workers if worker.key == key]

    def _resolve_idempotency_key(self, request):
        # Check the context's meta for an idempotency key. This will be used
        # to identify duplicate workflow submissions and handle them according
        # to their duplicate submission policy.
        
        # Defaults to the pipeline id
        default_idempotency_key = request.pipeline.id

        if type(request.meta.idempotency_key) == str:
            return request.meta.idempotency_key
            
        if len(request.meta.idempotency_key) == 0:
            return default_idempotency_key

        try:
            idempotency_key = ""
            # Set idemp key part delimiter. If only one item is in the list, delim is empty string
            part_delimiter = "." if len(request.meta.idempotency_key) > 1 else ""
            for constraint in request.meta.idempotency_key:
                (obj, prop) = constraint.split(".")
                key_part = None
                args_error = ""
                if obj != "args":
                    key_part = getattr(getattr(request, obj, EmptyObject()), prop, None)
                else:
                    # Access the value property if the object in the idemp key is args
                    arg_obj = getattr(request, obj, {}).get(prop, None)
                    key_part = arg_obj.value if arg_obj != None else None
                    args_error = ".value"

                if key_part == None:
                    raise AttributeError(f"Value not found for 'request.{obj}.{prop}{args_error}'")
                
                if idempotency_key == "":
                    idempotency_key = str(key_part)
                    continue

                idempotency_key = idempotency_key + part_delimiter + str(key_part)
            return idempotency_key

        except (AttributeError, TypeError) as e:
            logger.info(f"{lbuf('[SERVER]')} ERROR: Failed to resolve idempotency key from provided constraints. {str(e)}. Defaulted to pipeline id '{default_idempotency_key}'")
            return default_idempotency_key

    
