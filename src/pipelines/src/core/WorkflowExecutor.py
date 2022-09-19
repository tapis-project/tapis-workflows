import asyncio, uuid, os, logging

from core.TaskExecutorFactory import task_executor_factory as factory
from core.TaskResult import TaskResult
from core.events import (
    Event,
    EventPublisher,
    EventHandler,
    EventExchange
)
from core.events.types import (PIPELINE_ACTIVE, PIPELINE_COMPLETED, PIPELINE_ARCHIVING, PIPELINE_FAILED,
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
from core.middleware.archivers import (
    TapisSystemArchiver,
    S3Archiver,
    IRODSArchiver
)
from core.middleware.backends import TapisWorkflowsAPIBackend

from conf.configs import BASE_WORK_DIR
from utils import trunc_uuid, lbuffer_str as lbuf


PSTR = lbuf('[PIPELINE]')
TSTR = lbuf('[TASK]')

# NOTE TODO EventHandler Mixin is not necessary unless it is decided that a workflow
# executor can both publish to and subscibe to the exchange. That might make things
# a bit confusing.
class WorkflowExecutor(EventPublisher, EventHandler):
    """The Workflow Executor is responsible for processing and executing tasks for
    a single workflow. The entrypoint of Workflow Executor is a the asynchronous
    'run' method."""

    def __init__(self, _id=None):
        # Initializes the primary(and only)event exchange, enabling
        # publishers(the WorkflowExecutor and other event producers) to publish
        # events to it, triggering subscribers to handle those events. 
        EventPublisher.__init__(self, EventExchange())

        # # Add the Workflow Executor to its own exchange. This allows the workflow
        # # excutor to handle messages that it produces itself
        # # TODO Consider the implications of below
        # self.exchange.add_subscribers(
        #     self,
        #     [] # TODO add a handle method and all the callbacks
        # )

        self._id = _id if _id != None else uuid.uuid4()
        self._set_initial_state()

    async def run(self, request):
        """This method is the entrypoint for a workflow exection. It's invoked
        by the main Application instance when a workflow execution request is 
        recieved"""

        # Prepare the workflow executor, temporary results storage,
        # middleware(backends and archivers), queue the tasks, and generate 
        # the coroutines for each of the initial tasks 
        try:
            coroutines = self._pre_run(request)

            # Trigger the PIPELINE_ACTIVE event
            logging.info(f"{PSTR} {self.ctx.pipeline.id} [STARTED] {self.ctx.pipeline_run.uuid}")
            self.publish(Event(PIPELINE_ACTIVE, self.ctx))
        except Exception as e:
            # Trigger the terminal state callback.
            self._on_pipeline_terminal_state(failed=True)
            raise e
        
        # Run the coroutines
        await asyncio.gather(*coroutines)

    def _pre_run(self, request):
        # Resets the workflow executor to its initial state
        self._set_initial_state()

        # Validates and sets the request. All subsequent references to the request
        # should be made via 'self.ctx'
        self._set_context(request)

        # Prepare the file system for this pipeline
        self._prepare_fs()

        # Set the run id
        self.ctx.pipeline.run_id = self.ctx.pipeline_run.uuid

        # Backends are used to relay/persist updates about a pipeline run
        # and its tasks to some external resource
        # NOTE Currenly, the Tapis Workflows API is the only supported backend)
        self._initialize_backends()

        # Prepares archives to which the results of workflows will be persisted
        self._initialize_archivers()

        # Validate the tasks. Kill the pipeline if it contains cycles
        # or invalid dependencies
        try:
            self._set_tasks(self.ctx.pipeline.tasks)
        except Exception as e:
            raise e

        # Execute the initial tasks
        return self._prepare_queued_tasks()

    async def _execute_task(self, task):
        # NOTE The folowing line forces the async function to yield control to 
        # the event loop, allowing other async functions to run concurrently
        await asyncio.sleep(0)

        logging.info(f"{TSTR} {task.id} [ACTIVE]")

        try:
            if not self.is_dry_run:
                # Resolve the task executor and execute the task
                executor = factory.build(task, self.ctx, self.exchange)

                # Register the task executor
                self._register_executor(self.ctx.pipeline_run.uuid, task, executor)

                # create the task_execution object in Tapis
                self.publish(Event(TASK_ACTIVE, self.ctx, task=task))

                task_result = executor.execute()
            else:
                task_result = TaskResult(0, data={"task": task.id})
        except InvalidTaskTypeError as e:
            task_result = TaskResult(1, errors=[str(e)])
        except Exception as e:
            task_result = TaskResult(1, errors=[str(e)])

        # Get the next queued tasks if any
        coroutines = self._on_task_finish(task, task_result)

        # Await the coroutines to run them
        await asyncio.gather(*coroutines)

    def _get_initial_tasks(self, tasks):
        initial_tasks = [task for task in tasks if len(task.depends_on) == 0]

        if len(initial_tasks) == 0:
            raise MissingInitialTasksError(
                "Expected: 1 or more tasks with no dependencies - Found: 0"
            )

        return initial_tasks

    def _get_task(self, name):
        return next(filter(lambda a: a.name == name, self.tasks), None)

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

        self.tasks = tasks

        # Build a mapping between each task and the tasks that depend on them.
        # Doing this here saves us from having to perform the dependency
        # look-ups when queueing tasks, improving performance
        self.dependency_graph = {task.id: [] for task in self.tasks}

        for task in self.tasks:
            for parent_task in task.depends_on:
                self.dependency_graph[parent_task.id].append(task.id)

        # Detect loops in the graph
        try:
            initial_tasks = self._get_initial_tasks(self.tasks)
            graph_validator = GraphValidator()
            if graph_validator.has_cycle(self.dependency_graph, initial_tasks):
                raise CycleDetectedError("Cyclic dependencies detected")
        except (
            InvalidDependenciesError, CycleDetectedError, MissingInitialTasksError
        ) as e:
            raise e

        # Add all tasks to the queue
        self.queue = [ task for task in self.tasks ]

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
        self._deregister_executor(self.ctx.pipeline_run.uuid, task)
        
        # Run the on_pipeline_terminal_state callback if all tasks are complete
        if len(self.tasks) == len(self.finished):
            self._on_pipeline_terminal_state()
            return []

        # Execute all possible queued tasks
        return self._prepare_queued_tasks()

    def _prepare_fs(self):
        """Creates all of the directories necessary to run the pipeline, store
        temp files, and cache data"""
        # The pipeline root dir. All files and directories produced by a workflow
        # execution will reside here
        self.ctx.pipeline.root_dir = f"{BASE_WORK_DIR}{self.ctx.group.id}/{self.ctx.pipeline.id}/"
        os.makedirs(f"{self.ctx.pipeline.root_dir}", exist_ok=True)

        # Create the directories in which data between pipeline runs will be stored. This
        # will allow data to be reused or cached between runs
        self.ctx.pipeline.cache_dir = f"{self.ctx.pipeline.root_dir}cache/"
        os.makedirs(f"{self.ctx.pipeline.cache_dir}", exist_ok=True)

        # The directory for this particular run of the workflow
        self.ctx.pipeline.runs_dir = f"{self.ctx.pipeline.root_dir}runs/"
        self.ctx.pipeline.work_dir = f"{self.ctx.pipeline.runs_dir}{self.ctx.pipeline_run.uuid}/"
        os.makedirs(self.ctx.pipeline.work_dir, exist_ok=True)

    def _prepare_queued_tasks(self):
        coroutines = []
        for queued_task in self.queue:
            if self._task_is_ready(queued_task):
                self._remove_from_queue(queued_task)
                coroutines.append(self._execute_task(queued_task))

        return coroutines

    def _task_is_ready(self,task):
        # All tasks without dependencies are ready immediately
        if len(task.depends_on) == 0: return True

        for dep in task.depends_on:
            if dep.id not in self.finished:
                return False

        return True

    def _on_pipeline_terminal_state(self, failed=False):
        failed = failed or len(self.failed) > 0
        event_type = PIPELINE_FAILED if failed else PIPELINE_COMPLETED
    
        msg = "COMPLETE"
        if event_type == PIPELINE_FAILED: msg = "FAILED"

        logging.info(f"{PSTR} {self.ctx.pipeline.id} [{msg}] ")

        # Publish the PIPELINE_FAILED or COMPLETED event.
        # Triggers the archivers if there are any
        self.publish(Event(event_type, self.ctx))

        self._cleanup_run()

    def _on_task_completed(self, task, task_result):
        # Notify the subscribers that the task was completed
        self.publish(Event(TASK_COMPLETED, self.ctx, task=task, result=task_result))

        # Log the completion
        logging.info(f"{TSTR} {task.id} [COMPLETE]")

        # Add the task to the finished list
        self.finished.append(task.id)
        self.succeeded.append(task.id)

    def _on_task_fail(self, task, task_result):
        # Notify the subscribers that the task was completed
        self.publish(Event(TASK_FAILED, self.ctx, task=task, result=task_result))

        # Log the failure
        logging.info(f"{TSTR} {task.id} [FAILED]")

        # Add the task to the finished list
        self.finished.append(task.id)
        self.failed.append(task.id)

    def _remove_from_queue(self, task):
        self.queue.pop(self.queue.index(task))

    def _register_executor(self, run_id, task, executor):
        self.executors[f"{run_id}.{task.id}"] = executor

    def _deregister_executor(self, run_id, task):
        # Clean up the resources created by the task executor
        executor = self._get_executor(run_id, task)
        executor.cleanup()
        del self.executors[f"{run_id}.{task.id}"]
        logging.debug(f"{TSTR} {task.id} [EXECUTOR DEREGISTERED] {run_id}.{task.id}")

    def _get_executor(self, run_id, task):
        return self.executors[f"{run_id}.{task.id}"]

    def _cleanup_run(self):
        logging.info(f"{PSTR} {self.ctx.pipeline.id} [CLEANUP STARTED] {trunc_uuid(self.ctx.pipeline_run.uuid)}")
        # os.system(f"rm -rf {self.ctx.pipeline.work_dir}")
        logging.info(f"{PSTR} {self.ctx.pipeline.id} [CLEANUP COMPLETED] {trunc_uuid(self.ctx.pipeline_run.uuid)}")
        
        self._set_initial_state()
    
    # TODO Implement
    def terminate(self):
        logging.info("Termination signal detected")

    def _initialize_backends(self):
        # Initialize the backends. Backends are used to persist updates about the
        # pipeline and its tasks
        try:
            backend = TapisWorkflowsAPIBackend(self.ctx)
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

    def _initialize_archivers(self):
        # No archivers specified. Return
        if len(self.ctx.pipeline.archives) < 1: return

        # TODO Handle for multiple archives
        self.ctx.archive = self.ctx.pipeline.archives[0]

        ARCHIVERS_BY_TYPE = {
            "system": TapisSystemArchiver,
            "s3": S3Archiver,
            "irods": IRODSArchiver
        }

        # Get and initialize the archiver
        archiver = ARCHIVERS_BY_TYPE[self.ctx.archive.type]()

        # Add the backend as a subscriber to all events. When these events are "published"
        # by the workflow executor, the backend will be passed the message to handle it.
        self.add_subscribers(
            archiver,
            [PIPELINE_COMPLETED, PIPELINE_FAILED, PIPELINE_TERMINATED]
        )
    
    def _set_initial_state(self):
        self.failed = []
        self.succeeded = []
        self.finished = []
        self.queue = []
        self.tasks = []
        self.executors = {}
        self.dependency_graph = {}
        self.is_dry_run = False
        self.subscribers = {}
        self.ctx = None

    def _set_context(self, request):
        # TODO validate the request here. Maybe pydantic
        self.ctx = request
    
