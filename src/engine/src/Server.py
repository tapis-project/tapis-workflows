
import os, sys, time, logging
from threading import Thread

from typing import Literal, Union
from functools import partial
from json.decoder import JSONDecodeError


import pika

from pika.exceptions import AMQPError, ChannelClosedByBroker
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

from workers import WorkerPool
from workflows import WorkflowExecutor
from utils import deserialize_message, load_plugins
from errors import NoAvailableWorkers, WorkflowTerminated


logger = logging.getLogger("server")

# TODO Keep track of workflows submissions somehow so they can be terminated later
class Server:
    def __init__(self, inbound_queue_name, inbound_exchange_name):
        self.active_workers = []
        self.worker_pool = None
        self.plugins = []
        self.inbound_queue_name = inbound_queue_name
        self.inbound_exchange_name = inbound_exchange_name

    def __call__(self):
        """Initializes the dynamic worker pool composed of WorkflowExecutor
        workers, establishes a connection with RabbitMQ, creates the channel, 
        exchanges, and queues, and begins consuming from the inbound queue"""

        logger.info(f"Starting server")

        # Initialize plugins
        logger.info(f"Loading plugins {PLUGINS}")
        self.plugins = load_plugins(PLUGINS)

        # Create a worker pool that consists of the workflow executors that will
        # run the pipelines
        # TODO catch error for worker classes that dont inherit from "Worker"
        logger.info(f"Initializing workers {PLUGINS}")
        logger.info(f"Starting workers {STARTING_WORKERS}")
        logger.info(f"Max workers {MAX_WORKERS}")
        self.worker_pool = WorkerPool(
            worker_cls=WorkflowExecutor,
            starting_worker_count=STARTING_WORKERS,
            max_workers=MAX_WORKERS,
            worker_kwargs={
                "plugins": self.plugins
            }
        )
        logger.debug(f"Worker initialization complete")
        logger.debug(f"Available workers ({self.worker_pool.count()})")

        # Connect to the message broker
        connection = self._connect()

        # Create the channel, exchanges, and queues
        channel = connection.channel()

        # Inbound exchange and queue handles workflow submissions or resubmissions
        channel.exchange_declare(self.inbound_exchange_name, exchange_type=ExchangeType.fanout)
        inbound_queue = self._declare_queue(channel, self.inbound_queue_name, exclusive=True)
        channel.queue_bind(exchange=self.inbound_exchange_name, queue=inbound_queue.method.queue)

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

            logger.debug(f"Worker Engine Server started and ready to recieve workflow submissions.")

            channel.start_consuming()

            # Wait for all to complete
            for thread in threads:
                thread.join()

            connection.close()
            logger.info(f"Closing connection to message broker")

        # Occurs when basic_consume recieves the wrong args
        except ValueError as e:
            logger.critical(f"Critical Workflow Executor Error: {e}")
        # Cathes all ampq errors from .start_consuming()
        except AMQPError as e:
            logger.error(f"{e.__class__.__name__} - {e}")
        # Catch all other exceptions
        except Exception as e:
            logger.error(e)

    def _on_message_callback(self, channel, method, _, body, args):
        '''
        1. Deserializes and validates message from the inbound queue
        2. Provisions a worker from the worker pool
        3. Acks(or nacks) the message
        4. Registers the active worker to the server
        5. Dispatches the worker to process the worklfow submission request
        '''

        # Deserialze the message then convert to an object. If deserialization
        # fails, reject the message.
        try:
            request = WorkflowSubmissionRequest(**deserialize_message(body))
        except JSONDecodeError as e:
            logger.error(e)
            channel.basic_reject(method.delivery_tag, requeue=False)
            return
        
        # Resolve the idempotency key from the request
        request.idempotency_key = self._resolve_idempotency_key(request)

        # Run request middlewares over the workflow context
        # NOTE Request middlewares will very likely mutate the request
        try:
            for plugin in self.plugins:
                request = plugin.dispatch("request", request)
        except Exception as e:
            logger.error(e)
            channel.basic_reject(method.delivery_tag, requeue=False)
            return

        # Get the connection to the message queue for acks and nacks
        (connection, threads) = args

        # Get a workflow executor worker. If there are none available,
        # this will raise a "NoWorkersAvailabe" error which is handled
        # an the exception block below
        try:
            worker = self.worker_pool.check_out()
        except NoAvailableWorkers:
            logger.info(f"Insufficient workers available. RETRYING (10s)")
            connection.add_callback_threadsafe(
                partial(
                    self._ack_nack,
                    "nack",
                    channel,
                    method.delivery_tag,
                    delay=INSUFFICIENT_WORKER_RETRY_DELAY
                )
            )
            return
        

        # Register the active worker to the server
        worker = self._register_worker(request, worker)

        # Ack the message before dispatching the worker
        connection.add_callback_threadsafe(
            partial(
                self._ack_nack,
                "ack",
                channel,
                method.delivery_tag
            )
        )
        
        # Dispatch the worker (workflow executor) in a thread 
        t = Thread(target=self._dispatch, args=(worker, request))
        t.start()
        threads.append(t)

        # Clean up the stopped threads
        threads = [t for t in threads if t.is_alive()]

    def _dispatch(self, worker, request):
        """Handle the starting and termination of workflows"""
        
        directives = request.directives.keys()
        # Handle RUN directive
        if "RUN" in directives:
            try:
                threads = []
                
                if worker.can_start:
                    worker.start(request, threads)

                for t in threads:
                    t.join()
            except Exception as e:
                # Deregister and return executor back to the worker pool
                logger.error(e)

        # Handle TERMINATE directive
        if "TERMINATE_RUN" in directives:
            workers = self._get_active_workers(worker.key)
            for w in workers:
                # Terminates all of the pipeline runs for which their are uuids
                # in the TERMINATE_RUN directive array
                if worker.pipeline_run_uuid in directives["TERMINATE_RUN"]:
                    w.terminate()
                    # Deregister and return executor back to the worker pool
                    self._deregister_worker(w)
                    self.worker_pool.check_in(w)
    
        self._deregister_worker(worker)
        self.worker_pool.check_in(worker)

    def _ack_nack(
        self,
        ack_nack: Union[Literal["ack"], Literal["nack"]],
        channel,
        delivery_tag,
        delay=0
    ):
        if not channel.is_open:
            raise Exception(f"Channel closed: Cannot {'negatively acknowledge' if ack_nack == 'nack' else 'acknowledge'} the message")
        
        kwargs = {}
        if ack_nack == "nack":
            kwargs = {"requeue": False}
        
        # Wait the delay if necessary
        delay = abs(delay)
        if delay > 0:
            time.sleep(delay)

        # Call the acknowledge or negative acknowlege function
        fn = channel.basic_ack if ack_nack == "ack" else channel.basic_nack
        fn(delivery_tag, **kwargs)

    def _connect(self):
        # Initialize connection parameters with plain credentials
        connection_parameters = pika.ConnectionParameters(
            os.environ["BROKER_URL"],
            os.environ["BROKER_PORT"],
            "/",
            pika.PlainCredentials(
                os.environ["BROKER_USER"], os.environ["BROKER_PASSWORD"])
        )

        logger.info(f"Connecting to message broker")

        connected = False
        connection_attempts = 0
        while connected == False and connection_attempts <= MAX_CONNECTION_ATTEMPTS:
            try:
                connection_attempts = connection_attempts + 1
                connection = pika.BlockingConnection(connection_parameters)
                connected = True
            except Exception:
                logger.info(f"Connection failed ({connection_attempts})")
                time.sleep(CONNECTION_RETRY_DELAY)

        # Kill the build service if unable to connect
        if connected == False:
            logger.critical(f"Error: Maximum connection attempts reached ({MAX_CONNECTION_ATTEMPTS}). Unable to connect to message broker.")
            sys.exit(1)

        logger.info(f"Connected to message broker established")

        return connection

    # TODO handle for the case of multiple active workers with same
    # active worker key
    def _register_worker(self, request, worker):
        """Registers the worker to the Server. Handles duplicate workflow
        submissions"""
        # Set the idempotency key on the worker
        worker.key = request.idempotency_key
        
        # Set the pipeline run uuid on the worker
        worker.pipeline_run_uuid = request.pipeline_run.uuid

        # Check if there are workers running that have the same idempotency key
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
            logger.info(f"Warning: Duplicate Submission Policy of 'DEFER' not implemented. Handling as 'ALLOW'")
            pass
        elif policy == DUPLICATE_SUBMISSION_POLICY_ALLOW:
            pass
        
        worker.can_start = True
        self.active_workers.append(worker)

        return worker

    def _deregister_worker(self, worker, terminated=False):
        worker.key = None
        worker.current_run = None
        self.active_workers = [ w for w in self.active_workers if w.id != worker.id ]
        worker.reset(terminated=terminated)

    def _get_active_workers(self, idempotency_key):
        """
        Fetch all of the workers actively processing pipeline runs which have the
        proivded idempotency key
        """
        return [worker for worker in self.active_workers if worker.key == idempotency_key]
    
    def _declare_queue(self, channel, queue, exclusive=True):
        try:
            return channel.queue_declare(queue=queue, exclusive=exclusive)
        except ChannelClosedByBroker as e:
            logger.critical(f"Exclusive queue declaration error for queue '{queue}' | {e}")
            sys.exit(1)

    def _resolve_idempotency_key(self, request):
        # Check the context's meta for an idempotency key. This will be used
        # to identify duplicate workflow submissions and handle them according
        # to their duplicate submission policy.
        
        # Defaults to the pipeline id
        default_idempotency_key = request.pipeline_run.uuid

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
            logger.info(f"Warning: Failed to resolve idempotency key from provided constraints. {str(e)}. Defaulted to pipeline run uuid '{default_idempotency_key}'")
        except Exception as e:
            logger.info(f"Any unknown error occured resolving idempotency key | {str(e)}. Defaulted to pipeline run uuid '{default_idempotency_key}'")
 
        return default_idempotency_key
    
