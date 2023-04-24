import os, logging

from threading import Thread, Lock
from uuid import uuid4

from core.tasks.TaskExecutorFactory import task_executor_factory as factory
from owe_python_sdk.TaskResult import TaskResult
from owe_python_sdk.events import (
    Event,
    EventPublisher,
    EventExchange,
    ExchangeConfig
)
from owe_python_sdk.events.types import (
    PIPELINE_ACTIVE, PIPELINE_COMPLETED, PIPELINE_ARCHIVING, PIPELINE_FAILED,
    PIPELINE_PENDING, PIPELINE_SUSPENDED, PIPELINE_TERMINATED, TASK_ACTIVE,
    TASK_ARCHIVING, TASK_BACKOFF, TASK_COMPLETED, TASK_FAILED, TASK_PENDING,
    TASK_SUSPENDED, TASK_TERMINATED
)
from helpers.GraphValidator import GraphValidator # From shared
from errors.tasks import (
    InvalidTaskTypeError,
    MissingInitialTasksError,
    InvalidDependenciesError,
    CycleDetectedError,
)
# Tapis specific middleware
from contrib.tapis.middleware.event_handlers.backends import TapisWorkflowsAPIBackend
from contrib.tapis.middleware.event_handlers.archivers import TapisSystemArchiver

# Core middleware
from core.middleware.archivers import (
    S3Archiver,
    IRODSArchiver
)
from conf.constants import BASE_WORK_DIR
from core.workers import Worker
from core.state import ReactiveState, Hook, method_hook
from utils import lbuffer_str as lbuf, CompositeLogger


server_logger = logging.getLogger("server")

def interceptable(rollback=None): # Decorator factory
    def interceptable_decorator(fn): # Decorator
        def wrapper(self, *args, **kwargs): # Wrapper
            rollback_fn = getattr(self, (rollback or ""), None)
            try:
                # TODO figure out why setting reactive state in this decorator causes
                # a threading.Lock issue!
                res = fn(self, *args, **kwargs)
                if self.state.terminating or self.state.terminated:
                    rollback_fn and rollback_fn()

                return res
            except Exception as e:
                server_logger.debug(f"ID: {self.id} Exception in @interceptable: {self.id} | Terminating:{self.state.terminating}/Terminated:{self.state.terminated} | {e}")
                if self.state.terminating or self.state.terminated:
                    # Run the rollback function by the name provided in the
                    # interceptable decorator factory args
                    rollback_fn and rollback_fn()
                    return
                raise e
            
        return wrapper

    return interceptable_decorator

class WorkflowExecutor(Worker, EventPublisher):
    """The Workflow Executor is responsible for processing and executing tasks for
    a single workflow. The entrypoint of Workflow Executor is a the 'start' method.
    
    When initialized, the WorkflowExecutor creates an EventExchange to which
    EventPublishers can publish Events. EventHandlers can then be registered to the 
    EventExchange and handle the Events generated by the EventPublishers. The 
    WorkflowExecutor itself–as well as every TaskExecutor it spawns–are capable 
    of publishing Events to this exchange. Each WorkflowExecutor initialized by
    the Server is persitent, meaning that it is used throughout the lifetime
    of the Workflow Executor Server. After each run of a workflow, the
    WorkflowExecutor and its EventExchange are reset.
    """

    def __init__(self, _id=None, plugins=[]):
        # Initialze the Worker class
        Worker.__init__(self, _id)

        # Set the plugins
        self._plugins = plugins

        # Initializes the primary(and only)event exchange, enabling publishers
        # (the WorkflowExecutor and other Event producers) to publish Events to it,
        # triggering subscribers to handle those events. 
        EventPublisher.__init__(
            self,
            EventExchange(
                config=ExchangeConfig(
                    reset_on=[PIPELINE_COMPLETED, PIPELINE_FAILED, PIPELINE_TERMINATED]
                )
            )
        )

        # Thread lock
        self.lock = Lock()

        self.state = ReactiveState(
            hooks=[
                Hook(
                    self._on_change_state,
                    attrs=[] # No attrs means all state gets/sets triggers this hook
                ),
                # NOTE Not necessary to have this as a hook, but a good it's a good
                # demonstration of how ReactiveState works. Move logic from 
                # _on_change_ready_task to all spots where self.state.ready_tasks
                # is accessed or updated and remove this Hook
                Hook(
                    self._on_change_ready_task,
                    attrs=["ready_tasks"]
                )
            ],
            initial_state={
                "threads": [],
                "terminated": False,
                "terminating": False,
                "failed": [],
                "succeeded": [],
                "finished": [],
                "queue": [],
                "tasks": [],
                "executors": {},
                "dependency_graph": {},
                "is_dry_run": False,
                "ctx": None,
                "ready_tasks": [],
            },
            lock=self.lock
        )

        self._set_initial_state()
        
    # Logging formatters. Makes logs more useful and pretty
    def p_str(self, status): return f"{self.state.ctx.idempotency_key} {lbuf('[PIPELINE]')} {status} {self.state.ctx.pipeline.id}"
    def t_str(self, task, status): return f"{self.state.ctx.idempotency_key} {lbuf('[TASK]')} {status} {task.id}.{self.state.ctx.pipeline.id}"

    @interceptable()
    def start(self, ctx, threads):
        """This method is the entrypoint for a workflow exection. It's invoked
        by the main Server instance when a workflow submission is 
        recieved"""
        self.state.threads = threads

        try:
            # Prepare the workflow executor, temporary results storage,
            # middleware(backends and archivers), queue the tasks
            self._staging(ctx)

            # Get the first tasks
            unstarted_threads = self._fetch_ready_tasks()

            # Trigger the PIPELINE_ACTIVE event and log
            self.state.ctx.logger.info(self.p_str("STARTED"))
            self.publish(Event(PIPELINE_ACTIVE, self.state.ctx))
            
            # NOTE Triggers the hook _on_change_ready_task
            self.state.ready_tasks += unstarted_threads
        except Exception as e:
            # Trigger the terminal state callback.
            self._on_pipeline_terminal_state(event=PIPELINE_FAILED)
            raise e

    @interceptable()
    def _staging(self, ctx):
        # Resets the workflow executor to its initial state
        self._set_initial_state()
        
        # Validates and sets the context. All subsequent references to the context
        # should be made via 'self.state.ctx'
        self._set_context(ctx)
        
        # Prepare the file system for this pipeline
        self._prepare_fs()

        # Setup the server and the pipeline run loggers
        self._setup_loggers()

        # Set the run id
        self.state.ctx.pipeline.run_id = self.state.ctx.pipeline_run.uuid

        self.state.ctx.logger.info(f'{self.p_str("STAGING")} {self.state.ctx.pipeline.run_id}')

        # Backends are used to relay/persist updates about a pipeline run
        # and its tasks to some external resource
        # NOTE Currenly, the Tapis Workflows API is the only supported backend)
        self._initialize_backends()

        # Prepares archives to which the results of workflows will be persisted
        self._initialize_archivers()

        # Validate the tasks. Kill the pipeline if it contains cycles
        # or invalid dependencies
        try:
            self._set_tasks(self.state.ctx.pipeline.tasks)
        except Exception as e:
            raise e

    @interceptable()
    def _start_task(self, task):
        # Create a uuid for this task execution
        task.execution_uuid = str(uuid4())

        self.state.ctx.logger.info(self.t_str(task, "ACTIVE"))
        # create the task_execution object in Tapis
        self.publish(Event(TASK_ACTIVE, self.state.ctx, task=task))

        try:
            if not self.state.is_dry_run:
                # Resolve the task executor and execute the task
                executor = factory.build(task, self.state.ctx, self.exchange, plugins=self._plugins)
                # Register the task executor
                self._register_executor(self.state.ctx.pipeline_run.uuid, task, executor)
                
                task_result = executor.execute()
            else:
                task_result = TaskResult(0, data={"task": task.id})
        except InvalidTaskTypeError as e:
            self.state.ctx.logger.error(str(e))
            task_result = TaskResult(1, errors=[str(e)])
        except Exception as e:
            self.state.ctx.logger.error(str(e))
            task_result = TaskResult(1, errors=[str(e)])

        # Get the next queued tasks if any
        unstarted_threads = self._on_task_terminal_state(task, task_result)

        # NOTE Triggers hook _on_change_ready_task
        self.state.ready_tasks += unstarted_threads

    @interceptable()
    def _on_task_terminal_state(self, task, task_result):
        # Determine the correct callback to use
        callback = self._on_task_completed if task_result.success else self._on_task_fail

        # Call the callback. Marks task as completed or failed.
        # Also publishes a TASK_COMPLETED or TASK_FAILED based on the result
        callback(task, task_result)

        # TODO Check to see if the task has any more "retries" available.
        # If it does, requeue

        # Deregister the task executor. This cleans up the resources that were created
        # during the initialization and execution of the task executor
        # TODO NOTE the line below will throw and exception if task 
        # fails before registering the executor
        self._deregister_executor(self.state.ctx.pipeline_run.uuid, task)
        
        # Run the on_pipeline_terminal_state callback if all tasks are complete.
        if (
            len(self.state.tasks) == len(self.state.finished)
            or task_result.status != 0
        ):
            self._on_pipeline_terminal_state()
            return []

        # Execute all possible queued tasks
        return self._fetch_ready_tasks()

    @interceptable()
    def _on_pipeline_terminal_state(self, event=None):
        # No event was provided. Determine if complete or failed from number
        # of failed tasks
        if event == None:
            event = PIPELINE_FAILED if len(self.state.failed) > 0 else PIPELINE_COMPLETED
    
        msg = "COMPLETE"
        if event == PIPELINE_FAILED: msg = "FAILED"
        elif event == PIPELINE_TERMINATED: msg = "TERMINATED"

        self.state.ctx.logger.info(self.p_str(msg))

        # Publish the event. Triggers the archivers if there are any on ...COMPLETE
        self.publish(Event(event, self.state.ctx))
        
        self._cleanup_run()

        self._set_initial_state() 

    @interceptable()
    def _on_task_completed(self, task, task_result):
        # Notify the subscribers that the task was completed
        self.publish(Event(TASK_COMPLETED, self.state.ctx, task=task, result=task_result))

        # Log the completion
        self.state.ctx.logger.info(self.t_str(task, "COMPLETED"))

        # Add the task to the finished list
        self.state.finished.append(task.id)
        self.state.succeeded.append(task.id)

    @interceptable()
    def _on_task_fail(self, task, task_result):
        # Notify the subscribers that the task was completed
        self.publish(Event(TASK_FAILED, self.state.ctx, task=task, result=task_result))

        # Log the failure
        self.state.ctx.logger.info(self.t_str(task, "FAILED"))

        # Add the task to the finished list
        self.state.finished.append(task.id)
        self.state.failed.append(task.id)

    @interceptable()
    def _get_initial_tasks(self, tasks):
        initial_tasks = [task for task in tasks if len(task.depends_on) == 0]

        if len(initial_tasks) == 0:
            raise MissingInitialTasksError(
                "Expected: 1 or more tasks with no dependencies - Found: 0"
            )

        return initial_tasks

    @interceptable()
    def _set_tasks(self, tasks):
        # Create a list of the ids of the tasks
        task_ids = [task.id for task in tasks]

        # Determine if there are any invalid dependencies (dependencies not
        # included in the tasks list)
        invalid_deps = 0
        invalid_deps_message = ""
        for task in tasks:
            for dep in task.depends_on:
                if dep.id == task.id:
                    invalid_deps += 1
                    invalid_deps_message = (
                        invalid_deps_message
                        + f"#{invalid_deps} An task cannot be dependent on itself: {task.id} | "
                    )
                if dep.id not in task_ids:
                    invalid_deps += 1
                    invalid_deps_message = (
                        invalid_deps_message
                        + f"#{invalid_deps} Task '{task.id}' depends on non-existent task '{dep.id}'"
                    )

        if invalid_deps > 0:
            raise InvalidDependenciesError(invalid_deps_message)

        self.state.tasks = tasks

        # Build a mapping between each task and the tasks that depend on them.
        # Doing this here saves us from having to perform the dependency
        # look-ups when queueing tasks, improving performance
        self.state.dependency_graph = {task.id: [] for task in self.state.tasks}

        for task in self.state.tasks:
            for parent_task in task.depends_on:
                self.state.dependency_graph[parent_task.id].append(task.id)

        # Detect loops in the graph
        try:
            initial_tasks = self._get_initial_tasks(self.state.tasks)
            graph_validator = GraphValidator()
            if graph_validator.has_cycle(self.state.dependency_graph, initial_tasks):
                raise CycleDetectedError("Cyclic dependencies detected")
        except (
            InvalidDependenciesError, CycleDetectedError, MissingInitialTasksError
        ) as e:
            raise e

        # Add all tasks to the queue
        self.state.queue = [ task for task in self.state.tasks ]
    
    @interceptable()
    def _prepare_fs(self):
        """Creates all of the directories necessary to run the pipeline, store
        temp files, and cache data"""
        server_logger.debug(self.p_str("PREPPING FILESYSTEM"))
        # Set the directories
        # The pipeline root dir. All files and directories produced by a workflow
        # execution will reside here
        self.state.ctx.pipeline.root_dir = f"{BASE_WORK_DIR}{self.state.ctx.idempotency_key}/{self.state.ctx.pipeline.id}/"
        os.makedirs(f"{self.state.ctx.pipeline.root_dir}", exist_ok=True)

        # Create the directories in which data between pipeline runs will be stored. This
        # will allow data to be reused or cached between runs
        self.state.ctx.pipeline.cache_dir = f"{self.state.ctx.pipeline.root_dir}cache/"
        os.makedirs(f"{self.state.ctx.pipeline.cache_dir}", exist_ok=True)


        # The directory for this particular run of the workflow
        self.state.ctx.pipeline.work_dir = f"{self.state.ctx.pipeline.root_dir}runs/{self.state.ctx.pipeline_run.uuid}/"
        os.makedirs(self.state.ctx.pipeline.work_dir, exist_ok=True)
        
        # Set the work_dir on the WorkflowExecutor as well. Will be used for
        # cleaning up all the temporary files/dirs after the state is reset.
        # (Which means that ther will be no self.state.ctx.pipeline.work_dir)
        self.work_dir = self.state.ctx.pipeline.work_dir

    @interceptable()
    def _fetch_ready_tasks(self):
        ready_tasks = []
        threads = []
        for task in self.state.queue:
            if self._task_is_ready(task):
                ready_tasks.append(task)

        for task in ready_tasks:
            self._remove_from_queue(task)
            t = Thread(
                target=self._start_task,
                args=(task,)
            )
            threads.append(t)

        return threads

    @interceptable()
    def _task_is_ready(self, task):
        # All tasks without dependencies are ready immediately
        if len(task.depends_on) == 0: return True

        for dep in task.depends_on:
            if dep.id not in self.state.finished:
                return False

        return True

    @interceptable()
    def _remove_from_queue(self, task):
        len(self.state.queue) == 0 or self.state.queue.pop(self.state.queue.index(task))

    @interceptable()
    def _register_executor(self, run_id, task, executor):
        # TODO Might register an executor after termination in case of race condition
        self.state.executors[f"{run_id}.{task.id}"] = executor

    @interceptable()
    def _deregister_executor(self, run_id, task):
        # Clean up the resources created by the task executor
        executor = self._get_executor(run_id, task)
        executor.cleanup()
        del self.state.executors[f"{run_id}.{task.id}"]
        self.state.ctx.logger.debug(self.t_str(task, "EXECUTOR DEREGISTERED"))

    @interceptable()
    def _get_executor(self, run_id, task):
        return self.state.executors[f"{run_id}.{task.id}"]
    
    def _cleanup_run(self):
        self.state.ctx.logger.info(self.p_str("WORKFLOW EXECUTOR CLEANUP"))
        # os.system(f"rm -rf {self.work_dir}")
    
    def terminate(self):
        # NOTE SIDE EFFECT. Triggers the _on_terminate_hook in the
        # reactive state. Will prevent all gets and sets to self.state
        # thereafter
        self.state.terminating = True

    def reset(self, terminated=False):
        self.state.reset()
        self._set_initial_state()
        if terminated:
            self.state.terminated = True

    @interceptable()
    def _setup_loggers(self):
        # Create the logger. NOTE Directly instantiating a Logger object
        # is recommended against in the documentation, however it makes sense
        # in this using getLogger method will create a new Logger for each
        # pipeline run
        run_logger = logging.Logger(self.state.ctx.pipeline_run.uuid)

        handler = logging.FileHandler(f"{self.state.ctx.pipeline.work_dir}logs.txt")
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))

        run_logger.setLevel(logging.DEBUG)
        run_logger.addHandler(handler)

        self.state.ctx.logger = CompositeLogger([server_logger, run_logger])
        
    @interceptable(rollback="_reset_event_exchange")
    def _initialize_backends(self):
        self.state.ctx.logger.debug(self.p_str("INITIALIZING BACKENDS"))
        # Initialize the backends. Backends are used to persist updates about the
        # pipeline and its tasks
        try:
            backend = TapisWorkflowsAPIBackend(self.state.ctx)
        except Exception as e:
            self.state.ctx.logger.error(f"Could not intialize backend. Updates about the pipeline and its task will not be persisited. Error: {str(e)}")
            return

        # Add the backend as a subscriber to all events. When these events are "published"
        # by the workflow executor, the backend will be passed the message to handle it.
        self.add_subscribers(
            backend,
            [
                PIPELINE_ACTIVE, PIPELINE_COMPLETED, PIPELINE_ARCHIVING, PIPELINE_FAILED,
                PIPELINE_PENDING, PIPELINE_SUSPENDED, PIPELINE_TERMINATED, TASK_ACTIVE,
                TASK_ARCHIVING, TASK_BACKOFF, TASK_COMPLETED, TASK_FAILED, TASK_PENDING,
                TASK_SUSPENDED,  TASK_TERMINATED
            ]
        )

    @interceptable(rollback="_reset_event_exchange")
    def _initialize_archivers(self):
        self.state.ctx.logger.debug(self.p_str("INITIALIZING ARCHIVERS"))
        # No archivers specified. Return
        if len(self.state.ctx.pipeline.archives) < 1: return

        # TODO Handle for multiple archives
        self.state.ctx.archive = self.state.ctx.pipeline.archives[0]

        ARCHIVERS_BY_TYPE = {
            "system": TapisSystemArchiver,
            "s3": S3Archiver,
            "irods": IRODSArchiver
        }

        # Get and initialize the archiver
        archiver = ARCHIVERS_BY_TYPE[self.state.ctx.archive.type]()

        # Add the backend as a subscriber to all events. When these events are "published"
        # by the workflow executor, the backend will be passed the message to handle it.
        self.add_subscribers(
            archiver,
            [PIPELINE_COMPLETED, PIPELINE_FAILED, PIPELINE_TERMINATED]
        )

    def _set_initial_state(self):
        # Non-reactive state
        self.work_dir = None
        self.can_start = False

    @interceptable()
    def _set_context(self, ctx):
        # TODO validate the ctx here. Maybe pydantic
        self.state.ctx = ctx

    def _reset_event_exchange(self):
        self.exchange.reset()

    # Hooks
    @method_hook
    def _on_change_ready_task(self, state):
        for t in state.ready_tasks:
            t.start()
            state.threads.append(t)

        # Remove the ready tasks
        state.ready_tasks = []


    @method_hook
    def _on_change_state(self, state):
        """Cleans up the resources and state of the WorkflowExecutor when terminated.

        This is invoked by the WorkflowExecutors ReactiveState object when the intercept 
        condition is met, i.e. when the 'terminate' method changes 'self.state.terminated' 
        to True.

        NOTE
        NO thread locking should occur here (self.lock.acquire()).
        The ReactiveState object will acquire a thread lock with the WorkflowExecutor's
        Lock object(self.lock that was passed to it during it's instantiation) and release it
        once this function finishes
        """
        if not state.terminating or state.terminated:
            return

        self.publish(Event(PIPELINE_TERMINATED, self.state.ctx))

        self.state.ctx.logger.info(self.p_str("TERMINATING"))
        for _, executor in state.executors.items():
            executor.terminate()
    
        self._cleanup_run()