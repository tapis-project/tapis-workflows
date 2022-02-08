from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.services.UserService import user_service
from backend.views.responses.BaseResponse import BaseResponse
from backend.views.responses.http_errors import NotFound


class Accounts(RestrictedAPIView):
    def post(self, request):
        account = user_service.get_or_create(request.username)

        return BaseResponse(result={
            "account": account
        })

    def get(self, request):
        account = user_service.get(request.username)

        if account is None:
            return NotFound(message="Account not found")

        return BaseResponse(result={
            "account": account
        })