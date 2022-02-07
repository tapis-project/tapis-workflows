import json

from backend.views.APIView import APIView
from backend.services.Authenticator import authenticator
from backend.views.responses.http_errors import BaseResponse, BadRequest, Unauthorized
from utils.attrs import has_all_keys


class Auth(APIView):
    def post(self, request):
        body = json.loads(request.body)

        if not has_all_keys(body, ["username", "password"]):
            return BadRequest()

        authenticated = authenticator.authenticate(
            body,
            auth_method = "password"
        )

        if not authenticated:
            return Unauthorized(message=str(authenticator.error))

        return BaseResponse(
            message="successfully authenticated",
            result={
                "jwt": authenticator.get_jwt()
            }
        )
            