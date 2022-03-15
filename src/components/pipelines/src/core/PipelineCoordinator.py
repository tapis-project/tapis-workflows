import asyncio, time

from core.ActionExecutorResolver import action_executor_resolver as resolver
from core.ActionResult import ActionResult
from helpers.GraphValidator import GraphValidator
from errors.actions import InvalidActionTypeError, MissingInitialActionsError, InvalidDependenciesError, CycleDetectedError


class PipelineCoordinator:
    def __init__(self):
        self.failed = []
        self.successful = []
        self.finished = []
        self.queue = []
        self.actions = []
        self.dependencies = {}
        self.initial_actions = []
        self.is_dry_run = False

    async def start(self, message):
        start_message = f"Pipeline started: {message.pipeline.id}"
        if hasattr(message.directives, "DRY_RUN"):
            self.is_dry_run = True
            start_message = f"Pipline dry run: {message.pipeline.id}"

        print(start_message)

        # Validate the graph. Terminate the pipeline if it contains cycles
        # or invalid dependencies
        try:
            self._set_actions(message.pipeline.actions)
        except (InvalidDependenciesError, CycleDetectedError, MissingInitialActionsError) as e:
            print(str(e), f"\nPipeline terminated: {message.pipeline.id}")
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
        print(f"Running action {action.name}: {time.time()}")

        # The folowing line forces the async function to yield control to the event loop,
        # allowing other async functions to run concurrently
        await asyncio.sleep(0)
        
        try:
            # Resolve the action executor and execute the action
            if not self.is_dry_run:
                action_executor = resolver.resolve(action)
                action_result = action_executor.execute(action, message)
            else:
                action_result = ActionResult(0, data={"action": action.name})
        except InvalidActionTypeError as e:
            action_result = ActionResult(1, errors=[str(e)])
        
        # Get the next queued actions if any
        tasks = self._on_finish(action, action_result, message)

        # Await the tasks to run them
        await asyncio.gather(*tasks)
        
    def _get_initial_actions(self, actions):
        initial_actions = [ action for action in actions if len(action.depends_on) == 0 ]

        if len(initial_actions) == 0:
            raise MissingInitialActionsError("Expected: 1 or more actions with no dependencies - Found: 0")
        
        return initial_actions

    def _get_action(self, name):
        return next(filter(lambda a: a.name == name, self.actions), None)

    def _set_actions(self, actions):
        # Create a list of the names of actions
        action_names = [ action.name for action in actions ]

        # Determine if there are any invalid dependencies (dependencies not 
        # included in the actions list)
        invalid_deps = 0
        invalid_deps_message = ""
        for action in actions:
            for dep in action.depends_on:
                if dep.name == action.name:
                    invalid_deps += 1
                    invalid_deps_message = invalid_deps_message + f"#{invalid_deps} An action cannot be dependent on itself: {action.name} | "
                if dep.name not in action_names:
                    invalid_deps += 1
                    invalid_deps_message = invalid_deps_message + f"#{invalid_deps} Action '{action.name}' depends on non-existent action '{dep.name}'"

        if invalid_deps > 0:
            raise InvalidDependenciesError(invalid_deps_message)


        self.actions = actions

        # Build a mapping between each action and the actions that depend on them.
        # Doing this here saves us from having to perform the dependency
        # look-ups when queueing actions, improving performance
        self.dependencies = { action.name:[] for action in self.actions }

        for action in self.actions:
            for parent_action in action.depends_on:
                self.dependencies[parent_action.name].append(action.name)

        # Detect loops in the graph
        try:
            self.initial_actions = self._get_initial_actions(self.actions)
            graph_validator = GraphValidator()
            if graph_validator.has_cycle(self.dependencies, self.initial_actions):
                raise CycleDetectedError("Cyclical dependencies detected")
        except (InvalidDependenciesError, MissingInitialActionsError, CycleDetectedError) as e:
            raise e

    def _on_fail(self, action):
        print(f"Action '{action.name}' failed")
        self.failed.append(action.name)

    def _on_finish(self, action, action_result, message):
        # Add the action to the finished list
        self.finished.append(action.name)

        print(f"Finished action {action.name}: {time.time()}")
        print(f"Result for {action.name}: ", vars(action_result))

        pipeline_complete = True if len(self.actions) == len(self.finished) else False

        # TODO Raise FailedActionError if this action is not permitted to fail
        self._on_succeed(action) if action_result.success else self._on_fail(action)

        # Execute all possible queued actions
        tasks = []
        for queued_action in self.queue:
            can_run = True
            for dep in queued_action.depends_on:
                if dep.name not in self.finished:
                    can_run = False
                    break

            if can_run:
                self._remove_from_queue(queued_action)
                tasks.append(self._execute(queued_action, message))
       
        if pipeline_complete:
            print(f"Pipeline finished: {message.pipeline.id}")
            print(f"Fails: ({len(self.failed)})")
            print(f"Successes: ({len(self.successful)})")

        return tasks  

    def _on_succeed(self, action):
        self.successful.append(action.name)

    def _remove_from_queue(self, action):
        self.queue.pop(self.queue.index(action))