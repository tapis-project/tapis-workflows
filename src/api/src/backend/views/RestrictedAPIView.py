import json

from pydantic import ValidationError

from django.views import View
from django.views.decorators.csrf import csrf_exempt

from backend.views.http.responses.errors import MethodNotAllowed, UnsupportedMediaType, BadRequest, Unauthorized
from backend.views.http.requests import PreparedRequest
from backend.services.TapisAPIGateway import TapisAPIGateway
from backend.conf.constants import (
    TAPIS_TOKEN_HEADER,
    DJANGO_TAPIS_TOKEN_HEADER,
    PERMITTED_CONTENT_TYPES,
    PERMITTED_HTTP_METHODS
)


class RestrictedAPIView(View):
    # All methods on the RestrictedAPIView do not require a CSRF token
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        # Restrict to a set of http methods
        if request.method not in PERMITTED_HTTP_METHODS:
            return MethodNotAllowed()

        if request.method != "GET":
            # Accept only application/json for all non get methods
            if request.content_type not in PERMITTED_CONTENT_TYPES:
                return UnsupportedMediaType()

            # Ensure the body of the request is correctly encoded json
            try:
                self.request_body = json.loads(request.body)
            except json.JSONDecodeError:
                return BadRequest(message="Could not decode request body")
        
        # Set the request base url
        request.base_url = f"{request.scheme}://{request.get_host()}"

        # Set the request url
        request.url = request.base_url.rstrip("/") + "/" + request.path.lstrip("/")

        ### Auth start ###

        # Check that the X-TAPIS-TOKEN header is set
        if DJANGO_TAPIS_TOKEN_HEADER not in request.META:
            return BadRequest(message=f"Missing header: {TAPIS_TOKEN_HEADER}")

        # Initialize the tapis API Gateway based on the tenant provided
        self.tapis_api_gateway = TapisAPIGateway(request.base_url)

        # Authenticate the user and get the account
        request.authenticated = self.tapis_api_gateway.authenticate(
            {"jwt": request.META[DJANGO_TAPIS_TOKEN_HEADER]}, auth_method="jwt")

        request.tenant_id = self.tapis_api_gateway.tenant_id

        if not request.authenticated:
            return Unauthorized(self.tapis_api_gateway.error)

        request.username = str(self.tapis_api_gateway.get_username())

        ### Auth end ###

        return super(RestrictedAPIView, self).dispatch(request, *args, **kwargs)

    # Takes a pydantic base model and tries to validate it.
    # If it fails, a BadRequest Response is returned with the error message
    # generated by pydantic
    def prepare(self, request_schema):
        try:
            request_object = request_schema(**self.request_body)
        except ValidationError as e:
            errors = [ f"{error['type']}. {error['msg']}: {'.'.join(error['loc'])}" for error in json.loads(e.json())]
            failure_view = BadRequest(message="\n".join(errors))

            self.prepared_request = PreparedRequest(is_valid=False, failure_view=failure_view)
            return self.prepared_request

        self.prepared_request = PreparedRequest(body=request_object)
        return self.prepared_request

    

        

