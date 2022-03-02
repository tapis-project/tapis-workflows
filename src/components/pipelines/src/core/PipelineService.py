from core.ActionDispatcher import action_dispatcher
from core.ActionResult import ActionResult
from errors.actions import InvalidActionTypeError


class PipelineService:
    def __init__(self):
        self.failed_actions = []
        self.successful_actions = []

    def start(self, pipeline_context):
        print(f"Pipeline started: {pipeline_context.pipeline.id}")

        # Dispatch build actions. There should only be one
        self._dispatch_actions(
            pipeline_context.pipeline.actions, pipeline_context)

        print(f"Pipeline ended: {pipeline_context.pipeline.id}")

        # Reset the failed and successful actions
        self._reset()

    def _dispatch_actions(self, actions, pipeline_context):
        for action in actions:
            print(f"Action started: {action.name}")
            
            # Dispatch the action
            try:
                action_result = action_dispatcher.dispatch(action, pipeline_context)
                print("ActionResult", vars(action_result))
            except InvalidActionTypeError as e:
                print(e)
                action_result = ActionResult(1)
                
            
            # Set the actions_failed flag to True for all non-zero statuses
            if action_result.success == False:
                self.failed_actions.append(action)
                print(f"Action '{action.name}' failed")
                return

            print(f"Action ended: {action.name}")

    def _reset(self):
        self.failed_actions = []
        self.successful_actions = []

pipeline_service = PipelineService()