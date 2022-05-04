from core.BuildActionExecutorResolver import build_action_executor_resolver
from core.ActionExecutor import ActionExecutor
from executors.Webhook import Webhook
from errors.actions import InvalidActionTypeError


class ActionExecutorFactory:
    def build(self, action, message) -> ActionExecutor:
        try:
            fn = getattr(self, f"_{action.type}")
        except AttributeError:
            raise InvalidActionTypeError(
                f"Action '{action.name}' uses action type '{action.type}' which does not exist.",
                hint=f"Update Action with id=={action.id} to have one of the following types: [image_build, container_run, webhook_notification]",
            )

        return fn(action, message)

    def _image_build(self, action, message) -> ActionExecutor:
        # Returns a build executor for the specified image builder and
        # deployment type
        executor = build_action_executor_resolver.resolve(action)
        return executor(action, message)

    def _webhook_notification(self, action, message) -> ActionExecutor:
        return Webhook(action, message)

    def _container_run(self, action, message) -> ActionExecutor:
        return Webhook(action, message)


action_executor_factory = ActionExecutorFactory()
