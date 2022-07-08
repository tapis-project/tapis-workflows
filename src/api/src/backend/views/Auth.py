from backend.views.APIView import APIView
from backend.services.TapisAPIGateway import TapisAPIGateway
from backend.views.http.responses.errors import BaseResponse, Unauthorized
from backend.views.http.requests import AuthRequest


class Auth(APIView):
    def post(self, request):
        prepared_request = self.prepare(AuthRequest)

        if not prepared_request.is_valid:
            return prepared_request.failure_view

        body = prepared_request.body

        # Get the request base url
        request_url = f"{request.scheme}://{request.get_host()}"

        # Intialize the TapisAPIGateway
        api_gateway = TapisAPIGateway(request_url)

        authenticated = api_gateway.authenticate(
            {"username": body.username, "password": body.password},
            auth_method="password"
        )

        if not authenticated:
            return Unauthorized(message=api_gateway.error)

        return BaseResponse(
            message="successfully authenticated",
            result={
                "jwt": api_gateway.get_jwt()
            }
        )
            