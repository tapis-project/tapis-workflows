import os, logging

from threading import Thread, Lock

from core.TaskExecutorFactory import task_executor_factory as factory
from core.TaskResult import TaskResult
from core.events import (
    Event,
    EventPublisher,
    EventExchange,
    ExchangeConfig
)
from core.events.types import (
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
from errors import WorkflowTerminated
from core.middleware.backends import TapisWorkflowsAPIBackend
from core.middleware.archivers import (
    TapisSystemArchiver,
    S3Archiver,
    IRODSArchiver
)
from conf.constants import BASE_WORK_DIR
from core.workers import Worker
from core.state import ReactiveState, Hook, method_hook
from utils import lbuffer_str as lbuf


def terminable(fn):
    def wrapper(self, *args, **kwargs):
        try:
            # TODO figure out why setting reactive state in this decorator causes
            # a threading.Lock issue!
            # self.state.terminable_active = True
            res = fn(self, *args, **kwargs)
            # self.state.terminable_active = False
            return res
        except Exception as e:
            # self.state.terminable_active = False
            logging.debug(f"ID: {self.id} Exception in @terminable: {self.id} | Terminating:{self.state.terminating}/Terminated:{self.state.terminated} | {e}")
            if self.state.terminating or self.state.terminated:
                return
            raise e
        
    return wrapper

class WorkflowExecutor(Worker, EventPublisher):
    """The Workflow Executor is responsible for processing and executing tasks for
    a single workflow. The entrypoint of Workflow Executor is a the 'start' method.
    
    When initialized, the WorkflowExecutor creates an EventExchange to which
    EventPublishers can publish Events. EventHandlers can then be registered to the 
    EventExchange and handle the Events generated by the EventPublishers. The 
    WorkflowExecutor itself–as well as every TaskExecutor it spawns–are capable 
    of publishing Events to this exchange. Each WorkflowExecutor initialized by
    the Application is persitent, meaning that it is used throughout the lifetime
    of the Workflow Executor Application. After each run of a workflow, the
    WorkflowExecutor and its EventExchange are reset.
    """

    def __init__(self, _id=None):
        # Initialze the Worker class
        Worker.__init__(self, _id)

        # Initializes the primary(and only)event exchange, enabling publishers
        # (the WorkflowExecutor and other event producers) to publish events to it,
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
                Hook(
                    self._on_change_ready_task,
                    attrs=["ready_tasks"]
                ),
                # Hook(
                #     self._on_change_terminable_active,
                #     attrs=["terminable_active"]
                # )
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
                
                # TODO experimental
                "terminable_count": 0,
            },
            lock=self.lock
        )

        self._set_initial_state()

    # Logging formatters. Makes logs more useful and pretty
    def PSTR(self): return f"ID: {self.id} {lbuf('[PIPELINE]')}"
    def TSTR(self): return f"ID: {self.id} {lbuf('[TASK]')}"

    @terminable
    def start(self, ctx, threads):
        """This method is the entrypoint for a workflow exection. It's invoked
        by the main Application instance when a workflow submission is 
        recieved"""
        self.state.threads = threads

        try:
            # Prepare the workflow executor, temporary results storage,
            # middleware(backends and archivers), queue the tasks
            self._pre_run(ctx)

            # Get the first tasks
            unstarted_threads = self._fetch_ready_tasks()
            
            # NOTE Triggers the hook _on_change_ready_task
            self.state.ready_tasks += unstarted_threads
        except Exception as e:
            # Trigger the terminal state callback.
            self._on_pipeline_terminal_state(event=PIPELINE_FAILED)
            raise e

    @terminable
    def _pre_run(self, ctx):
        # Resets the workflow executor to its initial state
        self._set_initial_state()

        # Validates and sets the context. All subsequent references to the context
        # should be made via 'self.state.ctx'
        self._set_context(ctx)

        # Trigger the PIPELINE_ACTIVE event
        logging.info(f"{self.PSTR()} {self.state.ctx.pipeline.id} [STARTED] {self.state.ctx.pipeline_run.uuid}")
        self.publish(Event(PIPELINE_ACTIVE, self.state.ctx))

        # Prepare the file system for this pipeline
        self._prepare_fs()

        # Set the run id
        self.state.ctx.pipeline.run_id = self.state.ctx.pipeline_run.uuid

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

    @terminable
    def _start_task(self, task):
        logging.info(f"{self.TSTR()} {task.id} [ACTIVE]")
        # create the task_execution object in Tapis
        self.publish(Event(TASK_ACTIVE, self.state.ctx, task=task))

        try:
            if not self.state.is_dry_run:
                # Resolve the task executor and execute the task
                executor = factory.build(task, self.state.ctx, self.exchange)

                # Register the task executor
                self._register_executor(self.state.ctx.pipeline_run.uuid, task, executor)

                task_result = executor.execute()
            else:
                task_result = TaskResult(0, data={"task": task.id})
        except InvalidTaskTypeError as e:
            task_result = TaskResult(1, errors=[str(e)])
        except Exception as e:
            task_result = TaskResult(1, errors=[str(e)])

        # Get the next queued tasks if any
        unstarted_threads = self._on_task_finish(task, task_result)

        # NOTE Triggers hook _on_change_ready_task
        self.state.ready_tasks += unstarted_threads

    @terminable
    def _on_task_finish(self, task, task_result):
        # Determine the correct callback to use
        callback = self._on_task_completed if task_result.success else self._on_task_fail

        # Call the callback. Marks task as completed or failed.
        # Also publishes a TASK_COMPLETED or TASK_FAILED based on the result
        callback(task, task_result)

        # TODO Check to see if the task has any more "retries" available.
        # If it does, requeue

        # Deregister the task executor. This cleans up the resources that were created
        # during the initialization and execution of the task executor
        self._deregister_executor(self.state.ctx.pipeline_run.uuid, task)
        
        # Run the on_pipeline_terminal_state callback if all tasks are complete.
        # NOTE to prevent this from more than once, we put a check to see if state
        
        if len(self.state.tasks) == len(self.state.finished):
            self._on_pipeline_terminal_state()
            return []

        # Execute all possible queued tasks
        return self._fetch_ready_tasks()

    @terminable
    def _on_pipeline_terminal_state(self, event=None):
        # No event was provided. Determine if complete or failed from number
        # of failed tasks
        if event == None:
            event = PIPELINE_FAILED if len(self.state.failed) > 0 else PIPELINE_COMPLETED
    
        msg = "COMPLETE"
        if event == PIPELINE_FAILED: msg = "FAILED"
        elif event == PIPELINE_TERMINATED: msg = "TERMINATED"

        logging.info(f"{self.PSTR()} {self.state.ctx.pipeline.id} [{msg}] ")

        # Publish the event. Triggers the archivers if there are any on ...COMPLETED
        self.publish(Event(event, self.state.ctx))
        
        self._cleanup_run()

        self._set_initial_state() 

    @terminable
    def _on_task_completed(self, task, task_result):
        # Notify the subscribers that the task was completed
        self.publish(Event(TASK_COMPLETED, self.state.ctx, task=task, result=task_result))

        # Log the completion
        logging.info(f"{self.TSTR()} {task.id} [COMPLETE]")

        # Add the task to the finished list
        self.state.finished.append(task.id)
        self.state.succeeded.append(task.id)

    @terminable
    def _on_task_fail(self, task, task_result):
        # Notify the subscribers that the task was completed
        self.publish(Event(TASK_FAILED, self.state.ctx, task=task, result=task_result))

        # Log the failure
        logging.info(f"{self.TSTR()} {task.id} [FAILED]")

        # Add the task to the finished list
        self.state.finished.append(task.id)
        self.state.failed.append(task.id)

    @terminable
    def _get_initial_tasks(self, tasks):
        initial_tasks = [task for task in tasks if len(task.depends_on) == 0]

        if len(initial_tasks) == 0:
            raise MissingInitialTasksError(
                "Expected: 1 or more tasks with no dependencies - Found: 0"
            )

        return initial_tasks

    @terminable
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
    
    @terminable
    def _prepare_fs(self):
        """Creates all of the directories necessary to run the pipeline, store
        temp files, and cache data"""
        # The pipeline root dir. All files and directories produced by a workflow
        # execution will reside here
        self.state.ctx.pipeline.root_dir = f"{BASE_WORK_DIR}{self.state.ctx.group.id}/{self.state.ctx.pipeline.id}/"
        os.makedirs(f"{self.state.ctx.pipeline.root_dir}", exist_ok=True)

        # Create the directories in which data between pipeline runs will be stored. This
        # will allow data to be reused or cached between runs
        self.state.ctx.pipeline.cache_dir = f"{self.state.ctx.pipeline.root_dir}cache/"
        os.makedirs(f"{self.state.ctx.pipeline.cache_dir}", exist_ok=True)

        # The directory for this particular run of the workflow
        self.state.ctx.pipeline.runs_dir = f"{self.state.ctx.pipeline.root_dir}runs/"
        self.state.ctx.pipeline.work_dir = f"{self.state.ctx.pipeline.runs_dir}{self.state.ctx.pipeline_run.uuid}/"
        os.makedirs(self.state.ctx.pipeline.work_dir, exist_ok=True)

        # Set the work_dir to the WorkflowExecutor as well. Will be used for
        # cleaning up all the temporary files/dirs after the state is reset.
        # (Which means that ther will be no self.state.ctx.pipeline.work_dir)
        self.work_dir = self.state.ctx.pipeline.work_dir

    @terminable
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

    @terminable
    def _task_is_ready(self, task):
        # All tasks without dependencies are ready immediately
        if len(task.depends_on) == 0: return True

        for dep in task.depends_on:
            if dep.id not in self.state.finished:
                return False

        return True

    @terminable
    def _remove_from_queue(self, task):
        len(self.state.queue) == 0 or self.state.queue.pop(self.state.queue.index(task))

    @terminable
    def _register_executor(self, run_id, task, executor):
        # TODO Might register an executor after termination in case of race condition
        self.state.executors[f"{run_id}.{task.id}"] = executor

    @terminable
    def _deregister_executor(self, run_id, task):
        # Clean up the resources created by the task executor
        executor = self._get_executor(run_id, task)
        executor.cleanup()
        del self.state.executors[f"{run_id}.{task.id}"]
        logging.debug(f"{self.TSTR()} {task.id} [EXECUTOR DEREGISTERED] {run_id}.{task.id}")

    @terminable
    def _get_executor(self, run_id, task):
        return self.state.executors[f"{run_id}.{task.id}"]
    
    def _cleanup_run(self):
        logging.info(f"{self.PSTR()} ID: {self.id} [CLEANUP STARTED]")
        # os.system(f"rm -rf {self.work_dir}")
        logging.info(f"{self.PSTR()} ID: {self.id} [CLEANUP COMPLETED]")
    
    def terminate(self):
        self.publish(Event(PIPELINE_TERMINATED, self))
        # NOTE SIDE EFFECT. Triggers the _on_terminate_hook in the
        # reactive state. Will prevent all gets and sets to self.state
        # thereafter
        self.state.terminating = True

    def reset(self, terminated=False):
        self.state.reset()
        self._set_initial_state()
        if terminated:
            self.state.terminated = True
        

    @terminable
    def _initialize_backends(self):
        # Initialize the backends. Backends are used to persist updates about the
        # pipeline and its tasks
        try:
            backend = TapisWorkflowsAPIBackend(self.state.ctx)
        except Exception as e:
            logging.error(f"Could not intialize backend. Updates about the pipeline and its task will not be persisited. Error: {str(e)}")
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

    @terminable
    def _initialize_archivers(self):
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

    @terminable
    def _set_context(self, ctx):
        # TODO validate the ctx here. Maybe pydantic
        self.state.ctx = ctx

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

        logging.info(f"{self.PSTR()} {state.ctx.pipeline.id} [TERMINATING PIPELINE] {state.ctx.pipeline_run.uuid}")
        for _, executor in state.executors.items():
            executor.terminate()
    
        self._cleanup_run()

    # @method_hook
    # def _on_change_terminable_active(self, state):
    #     if state.terminable_active:
    #         state.terminable_count += 1
    #         print("Active terminables", state.terminable_count)
    #         return

    #     state.terminable_count -= 1
    #     print("Active terminables", state.terminable_count)
