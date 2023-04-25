from owe_python_sdk.middleware import RequestMiddleware
from owe_python_sdk.SchemaExtension import SchemaExtension

MIDDLEWARE_TYPES = [ "request", "archive", "backend", "task_executor", "schema_extension" ]

class Plugin:
    def __init__(self, name):
        self.name = name
        self.request_middlewares = []
        self.archive_middlewares = []
        self.backend_middlewares = []
        self.task_executors = {}
        self.schema_extensions = []

    def register(self, _type, middleware):
        if _type not in MIDDLEWARE_TYPES:
            raise Exception(f"Invalid Middleware type: Recieved '{_type}' | Expected oneOf {MIDDLEWARE_TYPES}")

        if _type == "request":
            if not isinstance(middleware, RequestMiddleware):
                raise Exception(f"Bad Middleware: {middleware.__class__.__name__} must be an instance of {RequestMiddleware.__class__.__name__}")
            self.request_middlewares.append(middleware)
        elif _type == "archive":
            self.archive_middlewares.append(middleware)
        elif _type == "backend":
            self.backend_middlewares.append(middleware)
        elif _type == "task_executor":
            if type(middleware) != dict:
                raise Exception(f"Middleware Registration Error: Task Executor middleware must be registered as a dict in which the key is the task type and value is the concrete Task Executor class(not an intance)")
            # TODO more logic to ensure key(s) is a string and val is a
            # subclass (not an instance) of TaskExecutor
            self.task_executors = {**self.task_executors, **middleware}
        elif _type == "schema_extension":
            if type(middleware) != SchemaExtension:
                raise Exception(f"Schema Extension Registration Error: Expected type 'SchemaExtension' | Recieved {type(middleware)}")
            self.schema_extensions.append(middleware)

    def dispatch(self, _type, ctx):
        if _type not in MIDDLEWARE_TYPES:
            raise Exception(f"Invalid Middleware type: Recieved '{_type}' | Expected oneOf {MIDDLEWARE_TYPES}")
        
        if _type == "request":
            request = ctx
            for request_middleware in self.request_middlewares:
                request = request_middleware(request)

        # TODO include logic for dispatching event handlers
            
        return request