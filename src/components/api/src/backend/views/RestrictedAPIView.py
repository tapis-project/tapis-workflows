import json

from typing import List

from django.views import View
from django.views.decorators.csrf import csrf_exempt

from backend.views.responses.http_errors import MethodNotAllowed, UnsupportedMediaType, BadRequest, Unauthorized
from backend.services.Authenticator import authenticator
from backend.views.validators.ValidationResult import ValidationResult


PERMITTED_HTTP_METHODS = [
    "GET", "POST", "PUT", "PATCH", "DETETE"]

PERMITTED_CONTENT_TYPES = [ "application/json" ]

TOKEN_HEADER = "X-TAPIS-TOKEN"

class RestrictedAPIView(View):
    # All methods on the RestrictedAPIView do not require a CSRF token
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

        request.username = str(authenticator.get_username())

        return super(RestrictedAPIView, self).dispatch(request, *args, **kwargs)

    def validate_request_body(self, body, properties: List[str]):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            failure_view = BadRequest(message="Could not decode request body")
            return ValidationResult(success=False, failure_view=failure_view, body=body)

        missing_properties = []
        for prop in properties:
            if prop not in body:
                missing_properties.append(prop)

        if len(missing_properties) > 0:
            failure_view = BadRequest(message=f"Request body missing properties: {[prop for prop in missing_properties]}")
            return ValidationResult(success=False, failure_view=failure_view, body=body)

        return ValidationResult(success=True, body=body)


        

