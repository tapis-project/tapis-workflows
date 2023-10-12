from owe_python_sdk.middleware import RequestMiddleware


class ArgsValidator(RequestMiddleware):
    def __call__(self, request):

        required_args = [
            "workflow_executor_access_token",
            "tapis_pipeline_owner",
            "tapis_tenant_id"
        ]
        
        for arg in required_args:
            value = request.args.get(arg, None)
            if value == None:
                raise Exception(f"Middleware Error: ArgsValidator: '{arg}' missing in request args")

        return request