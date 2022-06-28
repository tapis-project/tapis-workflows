import uuid

from typing import Dict
from backend.models import Credentials
from backend.conf.constants import SECRETS_TENANT, TAPIS_SERVICE_ACCOUNT, SECRETS_TENANT
from backend.helpers import tapis_service_api_gateway


class CredentialsService:
    def save(self, owner: str, data: Dict[str, str]):
        service_client = tapis_service_api_gateway.get_client()

        sk_id = f"workflows+{owner}+{uuid.uuid4()}"
        try:
            service_client.sk.writeSecret(
                secretType="user",
                secretName=sk_id,
                user=TAPIS_SERVICE_ACCOUNT,
                tenant=SECRETS_TENANT,
                data=data
            )
        except Exception as e:
            raise e

        credentials = Credentials.objects.create(sk_id=sk_id, owner=owner)
    
        return credentials

    def delete(self, sk_id: str):
        service_client = tapis_service_api_gateway.get_client()
        
        service_client.sk.deleteSecret(
            secretType="user",
            secretName=sk_id,
            user=TAPIS_SERVICE_ACCOUNT,
            tenant=SECRETS_TENANT,
            versions=[]
        )

        credentials = Credentials.objects.filter(sk_id=sk_id).first()
        if credentials is not None:
            credentials.delete()

    def get(self, sk_id: str):
        if Credentials.objects.filter(sk_id=sk_id).exists():
            return Credentials.objects.filter(sk_id=sk_id)[0]
        
        return None

    def get_secret(self, sk_id: str):
        service_client = tapis_service_api_gateway.get_client()
        
        return service_client.sk.readSecret(
            secretType="user",
            secretName=sk_id,
            user=TAPIS_SERVICE_ACCOUNT,
            tenant=SECRETS_TENANT,
            version=0
        ).secretMap.__dict__

    def _format_secret_name(self, secret_name: str):
        return secret_name.replace(" ", "-")
