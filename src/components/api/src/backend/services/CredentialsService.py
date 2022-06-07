import uuid

from typing import Dict

from tapipy.tapis import Tapis

from backend.models import Credentials
from backend.conf.constants import WORKFLOWS_SERVICE_URL, TAPIS_TENANT, WORKFLOWS_SERVICE_ACCOUNT, WORKFLOWS_SERVICE_PASSWORD

class CredentialsService:
    def __init__(self):
        # TODO convert to use service token
        self.client = Tapis(
            base_url=WORKFLOWS_SERVICE_URL,
            username=WORKFLOWS_SERVICE_ACCOUNT,
            password=WORKFLOWS_SERVICE_PASSWORD
        )
        
        self.client.get_tokens()

    def save(self, owner: str, data: Dict[str, str]):
        # TODO change secretType from "user" to "service" after creating the
        # workflows-svc account
        sk_id = f"workflows+{owner}+{uuid.uuid4()}"
        try:
            self.client.sk.writeSecret(
                secretType="user",
                secretName=sk_id,
                user=WORKFLOWS_SERVICE_ACCOUNT,
                tenant=TAPIS_TENANT,
                data=data
            )
        except Exception as e:
            raise e

        credentials = Credentials.objects.create(sk_id=sk_id, owner=owner)
    
        return credentials

    def delete(self, sk_id: str):
        self.client.sk.deleteSecret(
            secretType="user",
            secretName=sk_id,
            user=WORKFLOWS_SERVICE_ACCOUNT,
            tenant=TAPIS_TENANT,
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
        return self.client.sk.readSecret(
            secretType="user",
            secretName=sk_id,
            user=WORKFLOWS_SERVICE_ACCOUNT,
            tenant=TAPIS_TENANT,
            version=0
        ).secretMap.__dict__

    def _format_secret_name(self, secret_name: str):
        return secret_name.replace(" ", "-")
