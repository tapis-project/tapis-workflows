# import requests
from core.BuildActionDispatcherResolver import resolver
from errors.actions import InvalidActionTypeError


class ActionDispatcher:
    def dispatch(self, action, pipeline_context):
        try:
            fn = getattr(self, f"_{action.type}")
        except AttributeError:
            raise InvalidActionTypeError(
                f"Action '{action.name}' uses action type '{action.type}' which does not exist.",
                hint=f"Update Action with id=={action.id} to have one of the following types: [container_exec,webhook_notification]")

        return fn(action, pipeline_context)

    def _container_build(self, action, pipeline_context):
        # Returns a build dispatcher for the specified image builder and
        # deployment type
        dispatcher = resolver.resolve(action)

        # Dispatch the build action and return the status code
        return dispatcher.dispatch(action, pipeline_context)

    def _container_exec(self, action, pipeline_context):
        return 0

    def _webhook_notification(self, action, pipeline_context):
        return 0

action_dispatcher = ActionDispatcher()
