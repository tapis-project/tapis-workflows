class NotificationMiddleware:
    def __init__(self, handler, subsciptions=[]):
        self.handler = handler
        self.subscriptions = subsciptions