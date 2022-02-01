# import requests

class ActionDispatcher:
    def dispatch(self, action):
        action_type = action.type
        fn = getattr(self, action_type)
        return fn(action)

    def webhook(self, action):
        return 0

    def container(self, action):
        return 0

action_dispatcher = ActionDispatcher()
