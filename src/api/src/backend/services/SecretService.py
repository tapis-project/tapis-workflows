from typing import Dict

from backend.models import Secret
from backend.conf.constants import SECRETS_TENANT, TAPIS_SERVICE_ACCOUNT, SECRETS_TENANT
from backend.services.TapisServiceAPIGateway import TapisServiceAPIGateway
from backend.services.Service import Service
from backend.views.http.secrets import ReqCreateSecret


class SecretService(Service):
    def __init__(self):
        self.tapis_service_api_gateway = TapisServiceAPIGateway()
        Service.__init__(self)

    def create(self, tenant_id, owner, req_secret: ReqCreateSecret):
        service_client = self.tapis_service_api_gateway.get_client()

        sk_secret_name = f"tapis+{tenant_id}+workflows+{owner}+{req_secret.id}"
        try:
            service_client.sk.writeSecret(
                secretType="user",
                secretName=sk_secret_name,
                user=TAPIS_SERVICE_ACCOUNT,
                tenant=SECRETS_TENANT,
                data=req_secret.data,
                _tapis_set_x_headers_from_service=True
            )

            return Secret.objects.create(
                id=req_secret.id,
                description=req_secret.description,
                sk_secret_name=sk_secret_name,
                owner=owner,
                tenant_id=tenant_id
            )
        except Exception as e:
            raise e

    def delete(self, secret_id, tenant_id, owner):
        service_client = self.tapis_service_api_gateway.get_client()
        
        secret = Secret.objects.filter(id=secret_id, tenant_id=tenant_id, owner=owner).first()
        if secret is not None:
            secret.delete()

        service_client.sk.destroySecret(
            secretType="user",
            secretName=secret.sk_secret_name,
            user=TAPIS_SERVICE_ACCOUNT,
            tenant=SECRETS_TENANT,
            versions=[],
            _tapis_set_x_headers_from_service=True
        )

service = SecretService()
