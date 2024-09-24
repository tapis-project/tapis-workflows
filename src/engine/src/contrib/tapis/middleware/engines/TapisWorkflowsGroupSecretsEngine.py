from contrib.tapis.helpers import TapisServiceAPIGateway


class TapisWorkflowsGroupSecretsEngine:
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

    def __call__(self, pk, args):
        try:
            group_secret = self.service_client.workflows.getGroupSecret(
                _tapis_set_x_headers_from_service=True,
                _x_tapis_tenant=args["tapis_tenant_id"].value,
                _x_tapis_user=args["tapis_pipeline_owner"].value,
                group_id=args["tapis_workflows_group_id"].value,
                group_secret_id=pk
            )

            resp = self.service_client.sk.readSecret(
                secretType="user",
                secretName=group_secret.secret.sk_secret_name,
                user="workflows",
                tenant="admin",
                version=0,
                _tapis_set_x_headers_from_service=True
            )
            
            return resp.secretMap.__dict__["data"]
        except Exception as e:
            return None # TODO catch network error