from backend.views.RestrictedAPIView import RestrictedAPIView
from backend.services.UserService import user_service
from backend.views.http.responses.models import ModelResponse
from backend.views.http.responses.errors import NotFound


class Accounts(RestrictedAPIView):
    def post(self, request):
        account = user_service.get_or_create(request.username)

        return ModelResponse(account)

    def get(self, request):
        account = user_service.get(request.username)

        if account is None:
            return NotFound(message="Account not found")

        return ModelResponse(account)