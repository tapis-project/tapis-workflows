# import requests

class ActionDispatcher:
    def dispatch(self, action):
        action_type = action.type
        fn = getattr(self, f"_{action_type}")
        return fn(action)

    def _webhook(self, action):
        return 0

    def _container_exec(self, action):
        return 0

action_dispatcher = ActionDispatcher()
