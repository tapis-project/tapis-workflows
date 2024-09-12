import uuid

from typing import Dict

from backend.models import Credentials, Secret
from backend.conf.constants import SECRETS_TENANT, TAPIS_SERVICE_ACCOUNT, SECRETS_TENANT
from backend.services.TapisServiceAPIGateway import TapisServiceAPIGateway
from backend.services.Service import Service
from backend.views.http.secrets import ReqSecret


class CredentialsService(Service):
    def __init__(self):
        self.tapis_service_api_gateway = TapisServiceAPIGateway()
        Service.__init__(self)

    def save(self, owner: str, data: Dict[str, str]):
        service_client = self.tapis_service_api_gateway.get_client()

        sk_secret_name = f"tapis+workflows+{owner}+{uuid.uuid4()}"
        try:
            service_client.sk.writeSecret(
                secretType="user",
                secretName=sk_secret_name,
                user=TAPIS_SERVICE_ACCOUNT,
                tenant=SECRETS_TENANT,
                data=data,
                _tapis_set_x_headers_from_service=True
            )
        except Exception as e:
            raise e
        
        credentials = Credentials.objects.create(sk_id=sk_secret_name, owner=owner)
    
        return credentials

    def delete(self, sk_secret_name: str):
        service_client = self.tapis_service_api_gateway.get_client()
        
        service_client.sk.deleteSecret(
            secretType="user",
            secretName=sk_secret_name,
            user=TAPIS_SERVICE_ACCOUNT,
            tenant=SECRETS_TENANT,
            versions=[],
            _tapis_set_x_headers_from_service=True
        )

        credentials = Credentials.objects.filter(sk_id=sk_secret_name).first()
        if credentials is not None:
            credentials.delete()

    def get(self, sk_secret_name: str):
        if Credentials.objects.filter(sk_id=sk_secret_name).exists():
            return Credentials.objects.filter(sk_id=sk_secret_name)[0]
        
        return None

    def get_secret(self, sk_secret_name: str):
        service_client = self.tapis_service_api_gateway.get_client()
        
        try:
            res = service_client.sk.readSecret(
                secretType="user",
                secretName=sk_secret_name,
                user=TAPIS_SERVICE_ACCOUNT,
                tenant=SECRETS_TENANT,
                version=0,
                _tapis_set_x_headers_from_service=True
            )
            
            return res.secretMap.__dict__
        except Exception as e:
            return None # TODO catch network error

    def _format_secret_name(self, secret_name: str):
        return secret_name.replace(" ", "-")

service = CredentialsService()
