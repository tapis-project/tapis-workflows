import asyncio, uuid, os, logging

from core.TaskExecutorFactory import task_executor_factory as factory
from core.TaskResult import TaskResult
from core.archivers import (
    SystemArchiver,
    S3Archiver,
    IRODSArchiver
)
from helpers.GraphValidator import GraphValidator
from errors.tasks import (
    InvalidTaskTypeError,
    MissingInitialTasksError,
    InvalidDependenciesError,
    CycleDetectedError,
)
from errors.archives import ArchiveError
from conf.configs import BASE_WORK_DIR
from utils import trunc_uuid, lbuffer_str as lbuf


ARCHIVERS_BY_TYPE = {
    "system": SystemArchiver,
    "s3": S3Archiver,
    "irods": IRODSArchiver
}

PSTR = lbuf('[PIPELINE]')
TSTR = lbuf('[TASK]')

class PipelineExecutor:
    def __init__(self, _id=None):
        self.failed = []
        self.successful = []
        self.finished = []
        self.queue = []
        self.tasks = []
        self.executors = {}
        self.dependencies = {}
        self.initial_tasks = []
        self.is_dry_run = False

        # A unique id for the running executor
        self._id = _id if _id != None else uuid.uuid4()

    async def start(self, message):
        # Generate a unique id for this pipeline run
        run_id = uuid.uuid4()

        # Create the directory in which all files generated during this pipeline's execution
        # will be stored
        work_dir = f"{BASE_WORK_DIR}{message.group.id}/{message.pipeline.id}/{run_id}/"
        os.makedirs(work_dir, exist_ok=True)

        # Set the run id and scratch dir on the pipeline
        message.pipeline.run_id = run_id
        message.pipeline.work_dir = work_dir

        start_message = f"{PSTR} RUNNING: {message.pipeline.id}"
        if hasattr(message.directives, "DRY_RUN"):
            self.is_dry_run = True
            start_message = f"{PSTR} RUNNING(DRY-RUN): {message.pipeline.id}"

        logging.info(start_message)
        logging.info(f"{PSTR} RUN_ID: {run_id}")

        # Validate the graph. Terminate the pipeline if it contains cycles
        # or invalid dependencies
        try:
            self._set_tasks(message.pipeline.tasks, message)
        except (
            InvalidDependenciesError,
            CycleDetectedError,
            MissingInitialTasksError,
        ) as e:
            logging.exception(e)
            logging.error(f"\n{PSTR} TERMINATED: {message.pipeline.id}")
            return

        # Add all of the asynchronous coroutines to the queue
        self.queue = []
        for task in self.tasks:
            self.queue.append(task)

        # Execute the initial tasks
        coroutines = []
        for task in self.initial_tasks:
            self._remove_from_queue(task)
            coroutines.append(self._execute(task, message))

        await asyncio.gather(*coroutines)

    async def _execute(self, task, message):
        logging.info(f"{TSTR} RUNNING: '{task.id}'")

        # The folowing line forces the async function to yield control to the event loop,
        # allowing other async functions to run concurrently
        await asyncio.sleep(0)

        try:
            if not self.is_dry_run:
                # Resolve the task executor and execute the task
                executor = factory.build(task, message)

                # Register the task executor
                self._register_executor(message.pipeline.run_id, task, executor)

                task_result = executor.execute(self._on_finish)
            else:
                task_result = TaskResult(0, data={"task": task.id})
        except InvalidTaskTypeError as e:
            task_result = TaskResult(1, errors=[str(e)])

        # Get the next queued tasks if any
        coroutines = self._on_finish(task, task_result, message)

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

    def _set_tasks(self, tasks, message):
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
        self.dependencies = {task.id: [] for task in self.tasks}

        for task in self.tasks:
            for parent_task in task.depends_on:
                self.dependencies[parent_task.id].append(task.id)

        # Detect loops in the graph
        try:
            self.initial_tasks = self._get_initial_tasks(self.tasks)
            graph_validator = GraphValidator()
            if graph_validator.has_cycle(self.dependencies, self.initial_tasks):
                raise CycleDetectedError("Cyclic dependencies detected")
        except (
            InvalidDependenciesError,
            MissingInitialTasksError,
            CycleDetectedError,
        ) as e:
            raise e

    def _on_fail(self, task):
        logging.info(f"{TSTR} FAILED: '{task.id}'")
        self.failed.append(task.id)

    def _on_finish(self, task, task_result, message):
        # Add the task to the finished list
        self.finished.append(task.id)

        logging.info(f"{TSTR} COMPLETE: '{task.id}'")

        pipeline_complete = True if len(self.tasks) == len(self.finished) else False

        # TODO Raise FailedTaskError if this task is not permitted to fail
        self._on_succeed(task) if task_result.success else self._on_fail(task)

        # Deregister the task executor
        self._deregister_executor(message.pipeline.run_id, task)

        # Execute all possible queued tasks
        coroutines = []
        for queued_task in self.queue:
            can_run = True
            for dep in queued_task.depends_on:
                if dep.id not in self.finished:
                    can_run = False
                    break

            if can_run:
                self._remove_from_queue(queued_task)
                coroutines.append(self._execute(queued_task, message))

        if pipeline_complete:
            msg = "FAILED" if len(self.failed) > 0 else "COMPLETE"
            logging.info(f"{PSTR} {msg}: {message.pipeline.id}")
            logging.info(f"{PSTR} SUCCESSES: ({len(self.successful)})")
            logging.info(f"{PSTR} FAILS: ({len(self.failed)})")

            # Archive the results if any exist
            self._archive(message.pipeline, message.group, message.base_url)

            self._cleanup_run(message.pipeline)

            self._reset()

        return coroutines

    def _archive(self, pipeline, group, base_url):
        if len(pipeline.archives) < 1: return

        logging.info(f"{PSTR} ARCHIVING: {trunc_uuid(pipeline.run_id)}")
        # TODO Handle for multiple archives
        archive = pipeline.archives[0]

        # Get and initialize the archiver
        archiver = ARCHIVERS_BY_TYPE[archive.type]()

        # Archive the results
        try:
            archiver.archive(archive, pipeline, group, base_url)
        except ArchiveError as e:
            logging.error(f"{PSTR} ARCHIVING ERROR: {trunc_uuid(pipeline.run_id)}: {e.message}")
            return
        except Exception as e:
            logging.error(f"{PSTR} ARCHIVING ERROR: {trunc_uuid(pipeline.run_id)}: {e}")
            return

        logging.info(f"{PSTR} ARCHIVING COMPLETED: {trunc_uuid(pipeline.run_id)}")

    def _on_succeed(self, task):
        self.successful.append(task.id)

    def _remove_from_queue(self, task):
        self.queue.pop(self.queue.index(task))

    def _register_executor(self, run_id, task, executor):
        self.executors[f"{run_id}.{task.id}"] = executor

    def _deregister_executor(self, run_id, task):
        logging.debug(f"{TSTR} CLEANUP STARTED: {task.id}")
        # Clean up the resources created by the task executor
        executor = self._get_executor(run_id, task)
        executor.cleanup()
        del self.executors[f"{run_id}.{task.id}"]
        logging.debug(f"{TSTR} CLEANUP COMPLETED: {task.id}")

    def _get_executor(self, run_id, task):
        return self.executors[f"{run_id}.{task.id}"]

    def _cleanup_run(self, pipeline):
        logging.info(f"{PSTR} CLEANUP STARTED: {trunc_uuid(pipeline.run_id)}")
        # os.system(f"rm -rf {pipeline.work_dir}")
        logging.info(f"{PSTR} CLEANUP COMPLETED: {trunc_uuid(pipeline.run_id)}")

    def _reset(self):
        self.failed = []
        self.successful = []
        self.finished = []
        self.queue = []
        self.tasks = []
        self.executors = {}
        self.dependencies = {}
        self.initial_tasks = []
        self.is_dry_run = False
    
    def terminate(self):
        logging.info("Termination signal detected")