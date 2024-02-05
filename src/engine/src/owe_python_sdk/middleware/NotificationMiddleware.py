class NotificationMiddleware:
    def __init__(self, handler, subscriptions=[]):
        self.handler = handler
        self.subscriptions = subscriptions