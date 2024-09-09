from contrib.tapis.helpers import TapisServiceAPIGateway


class TapisSKSecretsEngine:
    def __init__(self):
        
        service_api_gateway = TapisServiceAPIGateway()
        self.service_client = service_api_gateway.get_client()
        
        # self._kwargs = {
        #     "_tapis_set_x_headers_from_service": True,
        #     "_x_tapis_tenant": ctx.args["tapis_tenant_id"].value,
        #     "_x_tapis_user": ctx.args["tapis_pipeline_owner"].value,
        #     "_tapis_headers": {
        #         "X-WORKFLOW-EXECUTOR-TOKEN": ctx.args["workflow_executor_access_token"].value
        #     }
        # }

    def __call__(self, tapis_tenant_id, sk_id):
        try:
            resp = self.service_client.sk.readSecret(
                secretType="user",
                secretName=sk_id,
                user="workflows",
                tenant=tapis_tenant_id,
                version=0,
                _tapis_set_x_headers_from_service=True
            )
            # ctx.args["tapis_tenant_id"].value
            return resp.secretMap.__dict__
        except Exception as e:
            return None # TODO catch network error