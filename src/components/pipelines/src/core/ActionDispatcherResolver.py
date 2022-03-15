from core.BuildActionDispatcherResolver import build_action_dispatcher_resolver
from core.ActionResult import ActionResult
from action_dispatchers.Webhook import dispatcher as webhook_dispatcher
from errors.actions import InvalidActionTypeError


class ActionDispatcherResolver:
    def resolve(self, action) -> ActionResult:
        try:
            fn = getattr(self, f"_{action.type}")
        except AttributeError:
            raise InvalidActionTypeError(
                f"Action '{action.name}' uses action type '{action.type}' which does not exist.",
                hint=f"Update Action with id=={action.id} to have one of the following types: [image_build, container_run, webhook_notification]")

        return fn(action)

    def _image_build(self, action) -> ActionResult:
        # Returns a build dispatcher for the specified image builder and
        # deployment type
        dispatcher = build_action_dispatcher_resolver.resolve(action)
        return dispatcher

    def _webhook_notification(self, action, _) -> ActionResult:
        dispatcher = webhook_dispatcher.dispatch(action)
        return dispatcher

    def _container_run(self, action) -> ActionResult:
        return ActionResult(status=0)

action_dispatcher_resolver = ActionDispatcherResolver()
