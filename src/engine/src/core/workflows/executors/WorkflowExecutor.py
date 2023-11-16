import os, logging, json

from threading import Thread, Lock
from uuid import uuid4
from pathlib import Path

from core.tasks.TaskExecutorFactory import task_executor_factory as factory
from owe_python_sdk.TaskResult import TaskResult
from owe_python_sdk.constants import STDERR, STDOUT
from owe_python_sdk.middleware.ArchiveMiddleware import ArchiveMiddleware
from owe_python_sdk.events import (
    Event,
    EventPublisher,
    EventExchange,
    ExchangeConfig
)
from owe_python_sdk.events.types import (
    PIPELINE_ACTIVE, PIPELINE_COMPLETED, PIPELINE_FAILED, PIPELINE_TERMINATED,
    PIPELINE_STAGING, TASK_STAGING, TASK_ACTIVE, TASK_COMPLETED, TASK_FAILED
)
from helpers import params_validator
from helpers.GraphValidator import GraphValidator # From shared
from helpers.TemplateMapper import TemplateMapper
from errors.tasks import (
    InvalidTaskTypeError,
    MissingInitialTasksError,
    InvalidDependenciesError,
    CycleDetectedError,
)
from core.middleware.archivers import S3Archiver, IRODSArchiver
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
                server_logger.debug(f"Workflow Termination Signal Detected: Terminating:{self.state.terminating}/Terminated:{self.state.terminated}")
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
    WorkflowExecutor itself--as well as every TaskExecutor it spawns--are capable 
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
                "failures_permitted": [],
                "succeeded": [],
                "finished": [],
                "queue": [],
                "tasks": [],
                "executors": {},
                "dependency_graph": {},
                "is_dry_run": False,
                "ready_tasks": [],
                "ctx": None,
            },
            lock=self.lock
        )

        self._set_initial_state()
        
    # Logging formatters. Makes logs more useful and pretty
    def p_str(self, status): return f"{lbuf('[PIPELINE]')} {self.state.ctx.idempotency_key} {status} {self.state.ctx.pipeline.id}"
    def t_str(self, task, status): return f"{lbuf('[TASK]')} {self.state.ctx.idempotency_key} {status} {self.state.ctx.pipeline.id}.{task.id}"

    @interceptable()
    def start(self, ctx, threads):
        """This method is the entrypoint for a workflow exection. It's invoked
        by the main Server instance when a workflow submission is 
        recieved"""
        self.state.threads = threads

        try:
            # Prepare the workflow executor, temporary results storage,
            # middleware(notification and archivers), queue the tasks
            self._staging(ctx)

            # Validate the submission args against the pipeline's parameters
            (validated, err) = params_validator(
                self.state.ctx.pipeline.params,
                self.state.ctx.args
            )

            if not validated:
                self._on_pipeline_terminal_state(event=PIPELINE_FAILED, message=err)
                return

            # Get the first tasks
            unstarted_threads = self._fetch_ready_tasks()

            # Log the pipeline status change
            self.state.ctx.logger.info(self.p_str("ACTIVE"))

            # Publish the active event
            self.publish(Event(PIPELINE_ACTIVE, self.state.ctx))
            
            # NOTE Triggers the hook _on_change_ready_task
            self.state.ready_tasks += unstarted_threads
        except Exception as e:
            # Trigger the terminal state callback.
            self._on_pipeline_terminal_state(event=PIPELINE_FAILED, message=str(e))

    @interceptable()
    def _staging(self, ctx):
        # Resets the workflow executor to its initial state
        self._set_initial_state()
        
        # Sets the execution context to the ReactiveState of the WorkflowExecutor.
        # All subsequent references to the context should be made via 'self.state.ctx'
        self._set_context(ctx)
        
        # Prepare the file system for this pipeline and handle pipeline templating
        self._prepare_pipeline()

        # Publish the PIPELINE_STAGING event
        # NOTE Events can only be published AFTER the '_prepare_pipeline' method is called
        # because the directory structure in which the logs do not exists until it is called.
        self.publish(Event(PIPELINE_STAGING, self.state.ctx))

        # Setup the server and the pipeline run loggers
        self._setup_loggers()

        # Prepare task objects and create the directory structure for task output and execution
        self._prepare_tasks()

        self.state.ctx.logger.info(f'{self.p_str("STAGING")} {self.state.ctx.pipeline_run.uuid}')

        # Notification handlers are used to relay/persist updates about a pipeline run
        # and its tasks to some external resource
        self._initialize_notification_handlers()

        # Prepares archives to which the results of workflows will be persisted
        self._initialize_archivers()

        # Validate the tasks. Kill the pipeline if it contains cycles
        # or invalid dependencies
        try:
            self._set_tasks(self.state.ctx.pipeline.tasks)
        except InvalidDependenciesError as e:
            self._on_pipeline_terminal_state(PIPELINE_FAILED, message=str(e))
        except Exception as e:
            print("ERROR HERE", e)
            self._on_pipeline_terminal_state(PIPELINE_FAILED, message=str(e))
        
    @interceptable()
    def _prepare_tasks(self):
        """This function adds information about the pipeline context to the task
        objects, prepares the file system for each task execution, handles task templating,
        and generates and registers the task executors that will be called to perform the
        work detailed in the task definition."""
        self.state.ctx.output = {}
        for task in self.state.ctx.pipeline.tasks:
            # Create an execution_uuid for each task in the pipeline
            task.execution_uuid = str(uuid4())

            # Paths to the workdir for the task inside the workflow engine container
            task.work_dir = f"{self.state.ctx.pipeline.work_dir}{task.id}/"
            task.exec_dir = f"{task.work_dir}src/"
            task.input_dir = f"{task.work_dir}input/"
            task.output_dir = f"{task.work_dir}output/"
            task.stdout = f"{task.output_dir}{STDOUT}"
            task.stderr = f"{task.output_dir}{STDERR}"

            # Paths to the workdir for the task inside the job container
            task.container_work_dir = "/mnt/open-workflow-engine/pipeline/task"
            task.container_exec_dir = f"{task.container_work_dir}/src/"
            task.container_input_dir = f"{task.container_work_dir}/input/"
            task.container_output_dir = f"{task.container_work_dir}/output/"

            # Paths to the workdir inside the nfs-server container
            task.nfs_work_dir = f"{self.state.ctx.pipeline.nfs_work_dir}{task.id}/"
            task.nfs_exec_dir = f"{task.nfs_work_dir}src/"
            task.nfs_input_dir = f"{task.nfs_work_dir}input/"
            task.nfs_output_dir = f"{task.nfs_work_dir}output/"

            # Create the task's directories
            self._prepare_task_fs(task)

            # Fetch task templates
            if task.uses != None:
                template_mapper = TemplateMapper(cache_dir=self.state.ctx.pipeline.git_cache_dir)
                try:
                    task = template_mapper.map(task, task.uses)
                except Exception as e:
                    # Trigger the terminal state callback.
                    self._on_pipeline_terminal_state(event=PIPELINE_FAILED, message=str(e))

            # Add a key to the output for the task
            self.state.ctx.output[task.id] = None

            # Resolve and register the task executor
            executor = factory.build(task, self.state.ctx, self.exchange, plugins=self._plugins)

            # Register the task executor
            self._register_executor(self.state.ctx.pipeline_run.uuid, task, executor)

    @interceptable()
    def _prepare_task_fs(self, task):
        # Create the base directory for all files and output created during this task execution
        os.makedirs(task.work_dir, exist_ok=True)

        # Create the exec dir for files created in support of the task execution
        os.makedirs(task.exec_dir, exist_ok=True)

        # Create the output dir in which the output of the task execution will be stored
        os.makedirs(task.output_dir, exist_ok=True)

        # Create the input dir in which the inputs to tasks will be staged
        os.makedirs(task.input_dir, exist_ok=True)

        # Create the stdout and stderr files
        Path(task.stdout).touch()
        Path(task.stderr).touch()

    @interceptable()
    def _start_task(self, task):
        # Log the task active
        self.state.ctx.logger.info(self.t_str(task, "ACTIVE"))

        # Publish the task active event
        self.publish(Event(TASK_ACTIVE, self.state.ctx, task=task))

        try:
            if not self.state.is_dry_run:
                # Get the task executor
                executor = self._get_executor(self.state.ctx.pipeline_run.uuid, task)
                
                task_result = executor.execute()

                self.state.ctx.output = {
                    **self.state.ctx.output,
                    **task_result.output
                }
            else:
                task_result = TaskResult(0, output={task.id: None})
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
        self._deregister_executor(self.state.ctx.pipeline_run.uuid, task)
        
        # Run the on_pipeline_terminal_state callback if all tasks are complete.
        if len(self.state.tasks) == len(self.state.finished):
            self._on_pipeline_terminal_state(event=PIPELINE_COMPLETED)
            return []
        
        if task_result.status != 0 and task.can_fail == False:
            self._on_pipeline_terminal_state(event=PIPELINE_FAILED)
            return []

        # Execute all possible queued tasks
        return self._fetch_ready_tasks()

    @interceptable()
    def _on_pipeline_terminal_state(self, event=None, message=""):
        # No event was provided. Determine if complete or failed from number
        # of failed tasks
        if event == None:
            event = PIPELINE_FAILED if len(self.state.failed) > 0 else PIPELINE_COMPLETED

        msg = "COMPLETED"

        if event == PIPELINE_FAILED: msg = "FAILED" + f" {message}"
        elif event == PIPELINE_TERMINATED: msg = "TERMINATED" + f" {message}"

        self.state.ctx.logger.info(self.p_str(msg))

        # Publish the event. Triggers the archivers if there are any on ...COMPLETE
        self.publish(Event(event, self.state.ctx))
        
        self._cleanup_run()

        self._set_initial_state() 

    @interceptable()
    def _on_task_completed(self, task, task_result):
        # Log the completion
        self.state.ctx.logger.info(self.t_str(task, "COMPLETED"))

        # Notify the subscribers that the task was completed
        self.publish(Event(TASK_COMPLETED, self.state.ctx, task=task, result=task_result))


        # Add the task to the finished list
        self.state.finished.append(task.id)
        self.state.succeeded.append(task.id)

    @interceptable()
    def _on_task_fail(self, task, task_result):
        # Log the failure
        self.state.ctx.logger.info(self.t_str(task, f"FAILED: {task_result.errors}"))

        # Notify the subscribers that the task was completed
        self.publish(Event(TASK_FAILED, self.state.ctx, task=task, result=task_result))

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
        print("START SET TASKS")
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
                        + f"#{invalid_deps} A task cannot be dependent on itself: {task.id} | "
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

        # Build 2 graphs:
        # The first is a mapping between each task and the tasks that depend on them,
        # and the second is a mapping between a task and tasks it depends on.
        # Suboptimal? Yes, Space complexity is ~O(n^2), but makes for easy lookups
        print("START CREATE DEPENDENCY MAP")
        graph_scaffold = {task.id: [] for task in self.state.tasks}
        self.state.dependency_graph = graph_scaffold
        self.state.reverse_dependency_graph = graph_scaffold
        for child_task in self.state.tasks:
            for parent_task in child_task.depends_on:
                self.state.dependency_graph[parent_task.id].append(child_task.id)
                self.state.reverse_dependency_graph[child_task.id].append(parent_task.id)
        print("END CREATE DEPENDENCY MAP")

        # Determine if a task can fail and set the tasks' can_fail flags.
        # A parent task is permitted to fail iff all of the following criteria are met:
        # - It has children
        # - All can_fail flags for a given parent task's children's task_dependency object == True 
        print("BEGIN SET CAN FAIL")
        for task in self.state.tasks:
            can_fail_flags = []
            for child_task_id in self.state.reverse_dependency_graph[task.id]:
                # Get the task
                child_task = self._get_task_by_id(child_task_id)
                dep = next(filter(lambda dep: dep.id == task.id, child_task.depends_on))
                can_fail_flags.append(dep.can_fail)

            # If the length of can_fail_flags == 0, then this task has no child tasks
            task.can_fail = False if len(can_fail_flags) == 0 else all(can_fail_flags)

        print("END SET CAN_FAIL")
        # Detect loops in the graph
        print("START CYCLE DETECTION")
        try:
            initial_tasks = self._get_initial_tasks(self.state.tasks)
            graph_validator = GraphValidator()
            if graph_validator.has_cycle(self.state.dependency_graph, initial_tasks):
                raise CycleDetectedError("Cyclic dependencies detected")
        except (
            InvalidDependenciesError, CycleDetectedError, MissingInitialTasksError
        ) as e:
            raise e
        print("END CYCLE DETECTION")

        # Add all tasks to the queue
        self.state.queue = [ task for task in self.state.tasks ]

    @interceptable()
    def _prepare_pipeline(self):
        # Create all of the directories needed for the pipeline to run and persist results and cache
        self._prepare_pipeline_fs()

        # template_mapper = TemplateMapper(cache_dir=self.state.ctx.pipeline.git_cache_dir)
        # if self.state.ctx.pipeline.uses != None:
        #     self.state.ctx.pipeline = template_mapper.map(
        #         self.state.ctx.pipeline,
        #         self.state.ctx.pipeline.uses
        #     )

    @interceptable()
    def _prepare_pipeline_fs(self):
        """Creates all of the directories necessary to run the pipeline, store
        temp files, and cache data"""
        server_logger.debug(self.p_str("PREPARING FILESYSTEM"))
        # Set the directories

        # References to paths on the nfs server
        self.state.ctx.pipeline.nfs_root_dir = f"/{self.state.ctx.idempotency_key}/"
        self.state.ctx.pipeline.nfs_cache_dir = f"{self.state.ctx.pipeline.nfs_root_dir}cache/"
        self.state.ctx.pipeline.nfs_docker_cache_dir = f"{self.state.ctx.pipeline.nfs_cache_dir}docker"
        self.state.ctx.pipeline.nfs_singularity_cache_dir = f"{self.state.ctx.pipeline.nfs_cache_dir}singularity"
        self.state.ctx.pipeline.nfs_git_cache_dir = f"{self.state.ctx.pipeline.nfs_cache_dir}git"
        self.state.ctx.pipeline.nfs_work_dir = f"{self.state.ctx.pipeline.nfs_root_dir}runs/{self.state.ctx.pipeline_run.uuid}/"

        # The pipeline root dir. All files and directories produced by a workflow
        # execution will reside here
        self.state.ctx.pipeline.root_dir = f"{BASE_WORK_DIR}{self.state.ctx.idempotency_key}/"
        os.makedirs(f"{self.state.ctx.pipeline.root_dir}", exist_ok=True)

        # Create the directories in which data between pipeline runs will be stored. This
        # will allow data to be reused or cached between runs
        self.state.ctx.pipeline.cache_dir = f"{self.state.ctx.pipeline.root_dir}cache/"
        os.makedirs(f"{self.state.ctx.pipeline.cache_dir}", exist_ok=True)

        # Create the docker and singularity cache dirs
        self.state.ctx.pipeline.docker_cache_dir = f"{self.state.ctx.pipeline.cache_dir}docker"
        os.makedirs(f"{self.state.ctx.pipeline.docker_cache_dir}", exist_ok=True)

        self.state.ctx.pipeline.singularity_cache_dir = f"{self.state.ctx.pipeline.cache_dir}singularity"
        os.makedirs(f"{self.state.ctx.pipeline.singularity_cache_dir}", exist_ok=True)

        # Create the github cache dir
        self.state.ctx.pipeline.git_cache_dir = f"{self.state.ctx.pipeline.cache_dir}git"
        os.makedirs(f"{self.state.ctx.pipeline.git_cache_dir}", exist_ok=True)

        # The directory for this particular run of the workflow
        self.state.ctx.pipeline.work_dir = f"{self.state.ctx.pipeline.root_dir}runs/{self.state.ctx.pipeline_run.uuid}/"
        os.makedirs(self.state.ctx.pipeline.work_dir, exist_ok=True)

        # The log file for this pipeline run
        self.state.ctx.pipeline.log_file = f"{self.state.ctx.pipeline.work_dir}logs.txt"
        
        # Set the work_dir on the WorkflowExecutor as well.
        # NOTE Will be used for cleaning up all the temporary files/dirs after 
        # the state is reset. (Which means that ther will be no self.state.ctx.pipeline.work_dir)
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
            dep_task = self._get_task_by_id(dep.id)
            if dep_task == None:
                raise Exception(f"Illegal dependency: Task with id '{dep.id}' doesn't exist")
            
            if dep_task.can_fail and dep_task.id in self.state.failed:
                continue

            if dep_task.id not in self.state.finished:
                return False

        return True
    
    @interceptable()
    def _get_task_by_id(self, task_id):
        return next(filter(lambda t: t.id == task_id,self.state.tasks), None)

    @interceptable()
    def _remove_from_queue(self, task):
        len(self.state.queue) == 0 or self.state.queue.pop(self.state.queue.index(task))

    @interceptable()
    def _register_executor(self, run_uuid, task, executor):
        self.state.executors[f"{run_uuid}.{task.id}"] = executor

    @interceptable()
    def _get_executor(self, run_uuid, task, default=None):
        return self.state.executors.get(f"{run_uuid}.{task.id}", None)

    @interceptable()
    def _deregister_executor(self, run_uuid, task):
        # Clean up the resources created by the task executor
        executor = self._get_executor(run_uuid, task)
        executor.cleanup()
        del self.state.executors[f"{run_uuid}.{task.id}"]
        # TODO use server logger below
        # self.state.ctx.logger.debug(self.t_str(task, "EXECUTOR DEREGISTERED"))

    @interceptable()
    def _get_executor(self, run_uuid, task):
        return self.state.executors[f"{run_uuid}.{task.id}"]
    
    def _cleanup_run(self):
        # TODO use server logger below
        #self.state.ctx.logger.info(self.p_str("WORKFLOW EXECUTOR CLEANUP"))
        pass
        # TODO remove comment below and pass above
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

        handler = logging.FileHandler(f"{self.state.ctx.pipeline.log_file}")
        handler.setFormatter(logging.Formatter("%(message)s"))

        run_logger.setLevel(logging.DEBUG)
        run_logger.addHandler(handler)
        self.state.ctx.logger = CompositeLogger([server_logger, run_logger])
        
    @interceptable(rollback="_reset_event_exchange")
    def _initialize_notification_handlers(self):
        self.state.ctx.logger.debug(self.p_str("INITIALIZING NOTIFICATION HANDLERS"))
        # Initialize the notification event handlers from plugins. Notification event handlers are used to persist updates about the
        # pipeline and its tasks
        for plugin in self._plugins:
            for middleware in plugin.notification_middlewares:
                try:
                    handler = middleware.handler(self.state.ctx)
                except Exception as e:
                    self.state.ctx.logger.error(f"Could not intialize notification middleware. Updates about the pipeline and its task will not be persisited. Error: {str(e)}")
                    return

                # Add the notification_handler as a subscriber to all events. When these events are "published"
                # by the workflow executor, the notification_handler will be passed the message to handle it.
                self.add_subscribers(
                    handler,
                    middleware.subscriptions
                )

    @interceptable(rollback="_reset_event_exchange")
    def _initialize_archivers(self):
        # No archivers specified. Return
        if len(self.state.ctx.archives) < 1: return

        self.state.ctx.logger.debug(self.p_str("INITIALIZING ARCHIVERS"))

        # TODO Handle for multiple archives
        self.state.ctx.archive = self.state.ctx.archives[0]

        archive_middlewares = [
            ArchiveMiddleware(
                "s3",
                handler=S3Archiver,
                subsciptions=[PIPELINE_COMPLETED, PIPELINE_FAILED, PIPELINE_TERMINATED]
            ),
            ArchiveMiddleware(
                "irods",
                handler=IRODSArchiver,
                subsciptions=[PIPELINE_COMPLETED, PIPELINE_FAILED, PIPELINE_TERMINATED]
            )
        ]
        
        # Add archive middleware from plugins to
        for plugin in self._plugins:
            archive_middlewares = [*archive_middlewares, *plugin.archive_middlewares]

        # Get and initialize the archiver
        middleware = next(filter(
            lambda middleware: middleware.type == self.state.ctx.archive.type,
            archive_middlewares
        ), None)

        if middleware == None:
            self.state.ctx.logger.error(self.p_str(f"FAILED TO INITIALIZE ARCHIVER: No Archive Middleware found with type {self.state.ctx.archive.type}")) 
            return
        
        try:
            handler = middleware.handler()
        except Exception as e:
            self.state.ctx.logger.error(f"Could not intialize archive middleware. Pipeline results will not be persisted. Error: {str(e)}")
            return
        
        # Add the archiver to the subscribers list
        self.add_subscribers(
            handler,
            middleware.subscriptions
        )

    def _set_initial_state(self):
        # Non-reactive state
        self.work_dir = None
        self.can_start = False

    @interceptable()
    def _set_context(self, ctx):
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
        
        # Log the terminating status
        self.state.ctx.logger.info(self.p_str("TERMINATING"))

        # Publish the termination event
        self.publish(Event(PIPELINE_TERMINATED, self.state.ctx))
        
        # Terminate the Task Executors
        for _, executor in state.executors.items():
            executor.terminate()
    
        self._cleanup_run()