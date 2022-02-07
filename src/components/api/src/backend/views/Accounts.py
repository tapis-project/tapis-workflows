import json

from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.services.UserService import user_service
from backend.views.responses.BaseResponse import BaseResponse
from backend.views.responses.http_errors import Unauthorized, BadRequest

class Accounts(RestrictedAPIView):
    def post(self, request):
        body = json.loads(request.body)

        return BaseResponse(result={
            "body": body
        })

    def get(self, request):
        return BaseResponse(result={
            "username": request.username
        })
