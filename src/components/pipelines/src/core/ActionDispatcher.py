# import requests
from core.BuildActionDispatcherResolver import resolver
from core.ActionResult import ActionResult
from action_dispatchers.Webhook import dispatcher as webhook_dispatcher
from errors.actions import InvalidActionTypeError


class ActionDispatcher:
    def dispatch(self, action, pipeline_context) -> ActionResult:
        try:
            fn = getattr(self, f"_{action.type}")
        except AttributeError:
            raise InvalidActionTypeError(
                f"Action '{action.name}' uses action type '{action.type}' which does not exist.",
                hint=f"Update Action with id=={action.id} to have one of the following types: [image_build, container_run, webhook_notification]")

        return fn(action, pipeline_context)

    def _image_build(self, action, pipeline_context) -> ActionResult:
        # Returns a build dispatcher for the specified image builder and
        # deployment type
        dispatcher = resolver.resolve(action)

        # Dispatch the build action and return the status code
        return dispatcher.dispatch(action, pipeline_context)

    def _webhook_notification(self, action, _) -> ActionResult:
        action_result = webhook_dispatcher.dispatch(action)
        return action_result

    def _container_run(self, action, pipeline_context) -> ActionResult:
        return ActionResult(status=0)

action_dispatcher = ActionDispatcher()
