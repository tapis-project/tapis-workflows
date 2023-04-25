from owe_python_sdk.middleware import RequestMiddleware


class ParamsValidator(RequestMiddleware):
    def __call__(self, request):

        required_params = [
            "workflow_executor_access_token",
            "tapis_pipeline_owner",
            "tapis_tenant_id"
        ]
        
        for param in required_params:
            if not hasattr(request.params, param):
                raise Exception(f"Middleware Error: ParamsValidator: '{param}' missing in request params")

        return request