import asyncio, time

from random import randint

from core.ActionDispatcher import action_dispatcher
from core.ActionResult import ActionResult
from helpers.GraphValidator import graph_validator
from errors.actions import InvalidActionTypeError, MissingInitialActionsError, InvalidDependenciesError, CycleDetectedError


class PipelineService:
    def __init__(self):
        self.failed = []
        self.successful = []
        self.finished = []
        self.queue = []
        self.actions = []
        self.dependencies = {}
        self.initial_actions = []

    async def start(self, pipeline_context):
        self._reset()

        print(f"Pipeline started: {pipeline_context.pipeline.id}")

        # Validate the graph. Terminate the pipeline if it contains cycles
        # or invalid dependencies
        try:
            self._set_actions(pipeline_context.pipeline.actions)
        except (InvalidDependenciesError, CycleDetectedError, MissingInitialActionsError) as e:
            print(str(e), f"\nPipeline terminated: {pipeline_context.pipeline.id}")
            return

        # Add all of the asynchronous tasks to the queue
        self.queue = []
        for action in self.actions:
            self.queue.append(action)


        # Dispatch the initial actions
        tasks = []
        for action in self.initial_actions:
            self._remove_from_queue(action)
            tasks.append(self._dispatch(action, pipeline_context))

        await asyncio.gather(*tasks)


    async def _dispatch(self, action, pipeline_context):
        print(f"Running action {action.name}: {time.time()}")
        await asyncio.sleep(0)
        
        # Dispatch the action
        try:
            action_result = action_dispatcher.dispatch(action, pipeline_context)
        except InvalidActionTypeError as e:
            action_result = ActionResult(1, errors=[str(e)])
        
        # Get the next queued actions if any
        tasks = self._on_finish(action, action_result, pipeline_context)

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
        invalid_dependencies = []
        for action in actions:
            for dep in action.depends_on:
                if dep.name not in action_names:
                    invalid_dependencies.append(dep.name)

        if len(invalid_dependencies) > 0:
            raise InvalidDependenciesError(f"Found {len(invalid_dependencies)} dependencies to actions that do not exist")

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
            if graph_validator.has_cycle(self.dependencies, self.initial_actions):
                raise CycleDetectedError("Cyclical dependencies detected")
        except (InvalidDependenciesError, MissingInitialActionsError, CycleDetectedError) as e:
            raise e

    def _on_fail(self, action):
        print(f"Action '{action.name}' failed")
        self.failed.append(action.name)

    def _on_finish(self, action, action_result, pipeline_context):
        # Add the action to the finished list
        self.finished.append(action.name)
        print(f"Finished action {action.name}: {time.time()}")
        # print(vars(action_result))
        # pipeline_complete = True if len(self.actions) == len(self.finished) else False

        # # TODO Raise FailedActionError if this action is not permitted to fail
        # self._on_succeed(action) if action_result.success else self._on_fail(action)

        # Dispatch all the queued actions
        tasks = []
        for queued_action in self.queue:
            can_run = True
            for dep in queued_action.depends_on:
                if dep.name not in self.finished:
                    can_run = False
                    break

            if can_run:
                self._remove_from_queue(queued_action)
                tasks.append(self._dispatch(queued_action, pipeline_context))
       
        # if pipeline_complete:
        #     print(f"Pipeline finished: {pipeline_context.pipeline.id}")
        #     print(f"Fails: ({len(self.failed)})")
        #     print(f"Successes: ({len(self.succeeded)})")

        return tasks  

    def _on_succeed(self, action):
        print(f"Action finished: {action.name}")
        self.succeeded.append(action.name)

    def _remove_from_queue(self, action):
        self.queue.pop(self.queue.index(action))

    def _reset(self):
        self.failed = []
        self.running = []
        self.succeeded = []
        self.queue = []
        self.actions = []
        self.dependencies = {}

pipeline_service = PipelineService()