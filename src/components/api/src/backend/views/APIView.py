from django.views import View

from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator

from backend.views.responses.http_errors import MethodNotAllowed, UnsupportedMediaType


PERMITTED_HTTP_METHODS = [
    "GET", "POST", "PUT", "PATCH", "DETETE"]

PERMITTED_CONTENT_TYPES = [ "application/json" ]

# @method_decorator(csrf_exempt, name="dispatch")
class APIView(View):
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

        return super(APIView, self).dispatch(request, *args, **kwargs)