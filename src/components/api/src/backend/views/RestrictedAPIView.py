from django.views import View
from django.views.decorators.csrf import csrf_exempt

from backend.views.responses.http_errors import MethodNotAllowed, UnsupportedMediaType, BadRequest, Unauthorized
from backend.services.Authenticator import authenticator
from backend.services.UserService import user_service


PERMITTED_HTTP_METHODS = [
    "GET", "POST", "PUT", "PATCH", "DETETE"]

PERMITTED_CONTENT_TYPES = [ "application/json" ]

TOKEN_HEADER = "X-TAPIS-TOKEN"

class RestrictedAPIView(View):
    # All methods on the APIView do not require a CSRF token
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if request.method not in PERMITTED_HTTP_METHODS:
            return MethodNotAllowed()

        # Accept only application/json
        if (
            request.method != "GET"
            and request.content_type not in PERMITTED_CONTENT_TYPES
        ):
            return UnsupportedMediaType()

        # Check that the X-TAPIS-TOKEN header is set
        DJANGO_TOKEN_HEADER = f"HTTP_{TOKEN_HEADER.replace('-', '_')}"
        if DJANGO_TOKEN_HEADER not in request.META:
            return BadRequest(message=f"Missing header: {TOKEN_HEADER}")

        # Authenticate the user and get the account
        authenticated = authenticator.authenticate(
            {"jwt": request.META[DJANGO_TOKEN_HEADER]}, auth_method="jwt")

        if not authenticated:
            return Unauthorized(authenticator.error)

        request.username = authenticator.get_username()

        return super(RestrictedAPIView, self).dispatch(request, *args, **kwargs)