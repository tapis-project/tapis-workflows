from backend.views.APIView import APIView
from backend.services.TapisAPIGateway import service as api_gateway
from backend.views.http.responses.errors import BaseResponse, Unauthorized
from backend.views.http.requests import AuthRequest


class Auth(APIView):
    def post(self, _):
        prepared_request = self.prepare(AuthRequest)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

        authenticated = api_gateway.authenticate(
            {"username": body.username, "password": body.password},
            auth_method = "password"
        )

        if not authenticated:
            return Unauthorized(message=api_gateway.error)

        return BaseResponse(
            message="successfully authenticated",
            result={
                "jwt": api_gateway.get_jwt()
            }
        )
            