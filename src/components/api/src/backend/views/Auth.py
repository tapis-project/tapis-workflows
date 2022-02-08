import json

from backend.views.APIView import APIView
from backend.services.Authenticator import authenticator
from backend.views.responses.http_errors import BaseResponse, BadRequest, Unauthorized
from utils.attrs import has_all_keys


class Auth(APIView):
    def post(self, request):
        result = self.validate_request_body(request.body, ["username", "password"])
        if not result.success:
            return result.failure_view

        body = result.body

        authenticated = authenticator.authenticate(
            body,
            auth_method = "password"
        )

        if not authenticated:
            return Unauthorized(message=authenticator.error)

        return BaseResponse(
            message="successfully authenticated",
            result={
                "jwt": authenticator.get_jwt()
            }
        )
            