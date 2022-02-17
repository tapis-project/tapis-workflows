from typing import Dict
from django.db import IntegrityError

from tapipy.tapis import Tapis
from django.forms.models import model_to_dict

from backend.models import Credential
from backend.settings import TAPIS_BASE_URL, TAPIS_TENANT, TAPIS_SERVICE_ACCOUNT, TAPIS_SERVICE_ACCOUNT_PASSWORD


class CredentialService:
    def __init__(self):
        self.client = Tapis(
            base_url=TAPIS_BASE_URL,
            username=TAPIS_SERVICE_ACCOUNT,
            password=TAPIS_SERVICE_ACCOUNT_PASSWORD
        )
        
        # TODO Cache the jwt
        self.client.get_tokens()

    def save(self, secret_name: str, group, data: Dict[str, str]):
        # TODO change secretType from "user" to "service" after creating the
        # cicd-pipelines-svc account
        sk_id = f"cicd-pipelines+{self._format_secret_name(secret_name)}"
        try:
            secret = self.client.sk.writeSecret(
                secretType="user",
                secretName=sk_id,
                user=TAPIS_SERVICE_ACCOUNT,
                tenant=TAPIS_TENANT,
                data=data
            )
        except Exception as e:
            raise e

        credential = Credential.objects.create(sk_id=sk_id, group=group)
    
        return (credential, secret, data)

    def delete(self, sk_id: str):
        self.client.sk.deleteSecret(
            secretType="user",
            secretName=sk_id,
            user=TAPIS_SERVICE_ACCOUNT,
            tenant=TAPIS_TENANT,
            versions=[]
        )

        credential = Credential.objects.filter(sk_id=sk_id).first()
        if credential is not None:
            credential.delete()

    def get(self, sk_id: str):
        if Credential.objects.filter(sk_id=sk_id).exists():
            return Credential.objects.filter(sk_id=sk_id)[0]
        
        return None

    def get_secret(self, sk_id: str):
        return self.client.sk.readSecret(
            secretType="user",
            secretName=sk_id,
            user=TAPIS_SERVICE_ACCOUNT,
            tenant=TAPIS_TENANT,
            version=0
        ).secretMap.__dict__

    def _format_secret_name(self, secret_name: str):
        return secret_name.replace(" ", "-")

cred_service = CredentialService()