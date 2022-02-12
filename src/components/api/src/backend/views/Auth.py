from backend.views.APIView import APIView
from backend.services.Authenticator import authenticator
from backend.views.http.responses.errors import BaseResponse, Unauthorized
from backend.views.http.requests import AuthRequest


class Auth(APIView):
    def post(self, _):
        prepared_request = self.prepare(AuthRequest)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

        authenticated = authenticator.authenticate(
            {"username": body.username, "password": body.password},
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
            