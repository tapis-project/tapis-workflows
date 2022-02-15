from backend.models import Credential
from backend.services.CredentialService import CredentialService

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.models import ModelListResponse

from backend.settings import DJANGO_TAPIS_TOKEN_HEADER


class Credentials(RestrictedAPIView):
    def get(self, request):
        credentials = Credential.objects.all()

        cred_service = CredentialService(request.META[DJANGO_TAPIS_TOKEN_HEADER])

        creds = []
        for cred in credentials:
            creds.append(cred_service.get_secret(cred.sk_id))

        return BaseResponse(result=creds)

    # TODO remove delete
    def delete(self, request):
        credentials = Credential.objects.all()

        cred_service = CredentialService(request.META[DJANGO_TAPIS_TOKEN_HEADER])
        for credential in credentials:
            cred_service.delete(credential.sk_id)

        return BaseResponse(message="Credentials deleted")