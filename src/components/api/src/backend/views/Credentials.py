from backend.models import Credentials
from backend.services.CredentialsService import CredentialService

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.views.http.responses.BaseResponse import BaseResponse
from backend.views.http.responses.models import ModelListResponse

from backend.conf.constants import DJANGO_TAPIS_TOKEN_HEADER


class Credentials(RestrictedAPIView):
    def get(self, request):
        credentials = Credentials.objects.all()

        cred_service = CredentialService(request.META[DJANGO_TAPIS_TOKEN_HEADER])

        creds = []
        for cred in credentials:
            creds.append(cred_service.get_secret(cred.sk_id))

        return BaseResponse(result=creds)

    # TODO remove delete
    def delete(self, request):
        credentials_list = Credentials.objects.all()

        cred_service = CredentialService(request.META[DJANGO_TAPIS_TOKEN_HEADER])
        for credentials in credentials_list:
            cred_service.delete(credentials.sk_id)

        return BaseResponse(message="Credentials deleted")