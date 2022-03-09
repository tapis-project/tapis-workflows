import asyncio

from core.ActionDispatcher import action_dispatcher
from core.ActionResult import ActionResult
from helpers.GraphValidator import graph_validator
from errors.actions import InvalidActionTypeError, MissingInitialActionsError, InvalidDependenciesError, CycleDetectedError


class PipelineService:
    def __init__(self):
        self.failed = []
        self.successful = []
        self.finished = []
        self.queued = []
        self.actions = []
        self.dependencies = {}
        self.event_loop = None
        self.initial_actions = []

    async def start(self, pipeline_context):
        self._reset()
        self.event_loop = asyncio.get_running_loop()

        print(f"Pipeline started: {pipeline_context.pipeline.id}")

        # Validate the graph. Terminate the pipeline if it contains cycles
        # or invalid dependencies
        terminated_message = f"\nPipeline terminated: {pipeline_context.pipeline.id}"
        try:
            self._set_actions(pipeline_context.pipeline.actions)
        except (InvalidDependenciesError, CycleDetectedError, MissingInitialActionsError) as e:
            print(str(e), terminated_message)
            return

        # Dispatch the initial actions
        for action in self.initial_actions:
            self._run(action, pipeline_context)

    def _dispatch(self, action, pipeline_context):
        print(f"Action started: {action.name}")
        
        # Dispatch the action
        try:
            action_result = action_dispatcher.dispatch(action, pipeline_context)
        except InvalidActionTypeError as e:
            action_result = ActionResult(1, errors=[str(e)])
            
        print(vars(action_result)) # TODO remove
        
        # Mark the action as finished
        self._on_finish(action, action_result, pipeline_context)
        
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

        print(self.dependencies)

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
        self.running.pop(self.running.index(action.name))
        pipeline_complete = True if len(self.actions) == len(self.finished) else False

        # # TODO Raise FailedActionError if this action is not permitted to fail
        # self._on_succeed(action) if action_result.success else self._on_fail(action)

        # Dispatch all the queued actions
        for name in self.queued:
            # Get the action from the actions list
            queued_action = self._get_action(name)

            can_run = True
            for dep in queued_action.depends_on:
                if dep.name not in self.finished:
                    can_run = False
                    break

            if can_run:
                self._run(queued_action, pipeline_context)

        if pipeline_complete:
            print(f"Pipeline finished: {pipeline_context.pipeline.id}")
            print(f"Fails: ({len(self.failed)})")
            print(f"Successes: ({len(self.succeeded)})")

    def _on_queue(self, action):
        if action.name not in self.queued:
            self.queued.append(action.name)
    
    def _run(self, action, pipeline_context):
        # Add the action to the running list
        self.running.append(action.name)

        # Remove the current running action from the queue if it is there
        if action.name in self.queued:
            self.queued.pop(self.queued.index(action.name))

        # Queue all the dependencies for this action
        for dep_name in self.dependencies[action.name]:
            self._on_queue(self._get_action(dep_name))

        self._dispatch(action, pipeline_context)

    def _on_succeed(self, action):
        print(f"Action finished: {action.name}")
        self.succeeded.append(action.name)

    def _reset(self):
        self.failed = []
        self.running = []
        self.succeeded = []
        self.queued = []
        self.actions = []
        self.dependencies = {}

pipeline_service = PipelineService()