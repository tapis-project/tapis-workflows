import asyncio, uuid, os, logging

from core.ActionExecutorFactory import action_executor_factory as factory
from core.ActionResult import ActionResult
from helpers.GraphValidator import GraphValidator
from errors.actions import (
    InvalidActionTypeError,
    MissingInitialActionsError,
    InvalidDependenciesError,
    CycleDetectedError,
)
from conf.configs import BASE_WORK_DIR


class PipelineCoordinator:
    def __init__(self):
        self.failed = []
        self.successful = []
        self.finished = []
        self.queue = []
        self.actions = []
        self.executors = {}
        self.dependencies = {}
        self.initial_actions = []
        self.is_dry_run = False

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

        start_message = f"Pipeline started: {message.pipeline.id}"
        if hasattr(message.directives, "DRY_RUN"):
            self.is_dry_run = True
            start_message = f"Pipline dry run: {message.pipeline.id}"

        logging.info(start_message)
        logging.info(f"Pipeline Run Id: {run_id}")

        # Validate the graph. Terminate the pipeline if it contains cycles
        # or invalid dependencies
        try:
            self._set_actions(message.pipeline.actions, message)
        except (
            InvalidDependenciesError,
            CycleDetectedError,
            MissingInitialActionsError,
        ) as e:
            logging.exception(e)
            logging.error(f"\nPipeline terminated: {message.pipeline.id}")
            return

        # Add all of the asynchronous tasks to the queue
        self.queue = []
        for action in self.actions:
            self.queue.append(action)

        # Execute the initial actions
        tasks = []
        for action in self.initial_actions:
            self._remove_from_queue(action)
            tasks.append(self._execute(action, message))

        await asyncio.gather(*tasks)

    async def _execute(self, action, message):
        logging.info(f"Starting action '{action.id}'")

        # The folowing line forces the async function to yield control to the event loop,
        # allowing other async functions to run concurrently
        await asyncio.sleep(0)

        try:
            if not self.is_dry_run:
                # Resolve the action executor and execute the action
                executor = factory.build(action, message)

                # Register the action executor
                self._register_executor(message.pipeline.run_id, action, executor)

                action_result = executor.execute(self._on_finish)
            else:
                action_result = ActionResult(0, data={"action": action.id})
        except InvalidActionTypeError as e:
            action_result = ActionResult(1, errors=[str(e)])

        # Get the next queued actions if any
        tasks = self._on_finish(action, action_result, message)

        # Await the tasks to run them
        await asyncio.gather(*tasks)

    def _get_initial_actions(self, actions):
        initial_actions = [action for action in actions if len(action.depends_on) == 0]

        if len(initial_actions) == 0:
            raise MissingInitialActionsError(
                "Expected: 1 or more actions with no dependencies - Found: 0"
            )

        return initial_actions

    def _get_action(self, name):
        return next(filter(lambda a: a.name == name, self.actions), None)

    def _set_actions(self, actions, message):
        # Create a list of the ids of the actions
        action_ids = [action.id for action in actions]

        # Determine if there are any invalid dependencies (dependencies not
        # included in the actions list)
        invalid_deps = 0
        invalid_deps_message = ""
        for action in actions:
            for dep in action.depends_on:
                if dep.id == action.id:
                    invalid_deps += 1
                    invalid_deps_message = (
                        invalid_deps_message
                        + f"#{invalid_deps} An action cannot be dependent on itself: {action.id} | "
                    )
                if dep.id not in action_ids:
                    invalid_deps += 1
                    invalid_deps_message = (
                        invalid_deps_message
                        + f"#{invalid_deps} Action '{action.id}' depends on non-existent action '{dep.id}'"
                    )

        if invalid_deps > 0:
            raise InvalidDependenciesError(invalid_deps_message)

        self.actions = actions

        # Build a mapping between each action and the actions that depend on them.
        # Doing this here saves us from having to perform the dependency
        # look-ups when queueing actions, improving performance
        self.dependencies = {action.id: [] for action in self.actions}

        for action in self.actions:
            for parent_action in action.depends_on:
                self.dependencies[parent_action.id].append(action.id)

        # Detect loops in the graph
        try:
            self.initial_actions = self._get_initial_actions(self.actions)
            graph_validator = GraphValidator()
            if graph_validator.has_cycle(self.dependencies, self.initial_actions):
                raise CycleDetectedError("Cyclical dependencies detected")
        except (
            InvalidDependenciesError,
            MissingInitialActionsError,
            CycleDetectedError,
        ) as e:
            raise e

    def _on_fail(self, action):
        logging.info(f"Action '{action.id}' failed")
        self.failed.append(action.id)

    def _on_finish(self, action, action_result, message):
        # Add the action to the finished list
        self.finished.append(action.id)

        logging.info(f"Finished action '{action.id}'")
        logging.debug(f"Result for '{action.id}': {vars(action_result)}")

        pipeline_complete = True if len(self.actions) == len(self.finished) else False

        # TODO Raise FailedActionError if this action is not permitted to fail
        self._on_succeed(action) if action_result.success else self._on_fail(action)

        # Deregister the action executor
        self._deregister_executor(message.pipeline.run_id, action)

        # Execute all possible queued actions
        tasks = []
        for queued_action in self.queue:
            can_run = True
            for dep in queued_action.depends_on:
                if dep.id not in self.finished:
                    can_run = False
                    break

            if can_run:
                self._remove_from_queue(queued_action)
                tasks.append(self._execute(queued_action, message))

        if pipeline_complete:
            self._cleanup_run(message.pipeline)
            logging.info(f"Pipeline finished: {message.pipeline.id}")
            logging.info(f"Fails: ({len(self.failed)})")
            logging.info(f"Successes: ({len(self.successful)})")

        return tasks

    def _on_succeed(self, action):
        self.successful.append(action.id)

    def _remove_from_queue(self, action):
        self.queue.pop(self.queue.index(action))

    def _register_executor(self, run_id, action, executor):
        self.executors[f"{run_id}.{action.id}"] = executor

    def _deregister_executor(self, run_id, action):
        logging.debug(f"Cleaning up executor for action '{action.id}'")
        # Clean up the resources created by the action executor
        executor = self._get_executor(run_id, action)
        executor.cleanup()
        del self.executors[f"{run_id}.{action.id}"]

    def _get_executor(self, run_id, action):
        return self.executors[f"{run_id}.{action.id}"]

    def _cleanup_run(self, pipeline):
        logging.info("Cleaning up pipeline resources")
        # os.system(f"rm -rf {pipeline.work_dir}")
