from core.BuildActionExecutorResolver import build_action_executor_resolver
from core.ActionResult import ActionResult
from executors.Webhook import executor as webhook_executor
from errors.actions import InvalidActionTypeError


class ActionExecutorResolver:
    def resolve(self, action) -> ActionResult:
        try:
            fn = getattr(self, f"_{action.type}")
        except AttributeError:
            raise InvalidActionTypeError(
                f"Action '{action.name}' uses action type '{action.type}' which does not exist.",
                hint=f"Update Action with id=={action.id} to have one of the following types: [image_build, container_run, webhook_notification]")

        return fn(action)

    def _image_build(self, action) -> ActionResult:
        # Returns a build executor for the specified image builder and
        # deployment type
        executor = build_action_executor_resolver.resolve(action)
        return executor

    def _webhook_notification(self, _) -> ActionResult:
        return webhook_executor

    def _container_run(self, _) -> ActionResult:
        return webhook_executor

action_executor_resolver = ActionExecutorResolver()
