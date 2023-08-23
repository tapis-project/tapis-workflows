class ArchiveMiddleware:
    def __init__(self, _type, handler, subsciptions=[]):
        self.type = _type
        self.handler = handler
        self.subscriptions = subsciptions