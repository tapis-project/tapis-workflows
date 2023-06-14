import json

from pydantic import ValidationError
from tapisservice import errors

from django.views import View
from django.views.decorators.csrf import csrf_exempt

from backend.views.http.responses.errors import MethodNotAllowed, UnsupportedMediaType, BadRequest, Unauthorized, ServerError
from backend.views.http.responses import NoContentResponse
from backend.views.http.requests import PreparedRequest
from backend.services.TapisAPIGateway import TapisAPIGateway
from backend.services.TapisServiceAPIGateway import TapisServiceAPIGateway
from backend.utils import one_in
from backend.conf.constants import (
    TAPIS_TOKEN_HEADER,
    DJANGO_TAPIS_TOKEN_HEADER,
    PERMITTED_CONTENT_TYPES,
    PERMITTED_HTTP_METHODS,
    TAPIS_DEV_URL,
    LOCAL_DEV_HOSTS,
    PERMITTED_SERVICES
)


class RestrictedAPIView(View):
    # All methods on the RestrictedAPIView do not require a CSRF token
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        # Restrict to a set of http methods
        if request.method not in PERMITTED_HTTP_METHODS:
            return MethodNotAllowed()

        # NOTE CORS preflight check entails a request and OPTIONS method to
        # ensure CORS is enabled. Sending a 204 content enables the preflight
        # request to succeed
        if request.method == "OPTIONS":
            return NoContentResponse(message="No content")

        if request.method != "GET":
            # Accept only application/json for all non get methods
            if request.content_type not in PERMITTED_CONTENT_TYPES:
                return UnsupportedMediaType(f"Unsupported media type. Received: {request.content_type} | Expected one of {PERMITTED_CONTENT_TYPES}")

            # Handle for requests that are non-GET and no request body sent
            request_body = request.body
            if request.content_type == None:
                request_body = b""

            # Ensure the body of the request is correctly encoded json
            try:
                self.request_body = json.loads(
                    b"{}" if request_body == b"" else request_body)
            except json.JSONDecodeError:
                return BadRequest(message="Could not decode request body")
        
        # Set the request base url. If the request comes from a local source,
        # change the base_url to the dev url
        request.base_url = f"{request.scheme.replace('https', 'http')}s://{request.get_host()}"
        if one_in(LOCAL_DEV_HOSTS, request.base_url):
            request.base_url = TAPIS_DEV_URL

        # Set the request url. This is the full url to where the request was sent
        request.url = request.base_url.rstrip("/") + "/" + request.path.lstrip("/")

        ### Auth start ###

        # Check that the X-TAPIS-TOKEN header is set
        if DJANGO_TAPIS_TOKEN_HEADER not in request.META:
            return BadRequest(message=f"Missing header: {TAPIS_TOKEN_HEADER}")

        # Initialize the tapis API Gateway based on the tenant provided
        self.tapis_api_gateway = TapisAPIGateway(request.base_url)
        
        # Set the tenant_id on the request
        request.tenant_id = self.tapis_api_gateway.tenant_id

        # Authenticate the user and get the account
        jwt = request.META[DJANGO_TAPIS_TOKEN_HEADER]
        request.authenticated = self.tapis_api_gateway.authenticate(
            {"jwt": jwt},
            auth_method="jwt"
        )

        # Try to authenticate as a service
        service_username = None
        if not request.authenticated:
            try:
                service_client = TapisServiceAPIGateway(jwt=jwt).get_client()
                claims = service_client.validate_token(jwt)
            except errors.AuthenticationError as e:
                return Unauthorized(f"Unable to validate the Tapis token; details: {e}")
            except Exception as e:
                return Unauthorized(f"Unable to validate the Tapis token; details: {e}")
            
            # Verify the the validate service request is from one of the permitted services
            service_username = claims["tapis/username"] if claims["tapis/username"] in PERMITTED_SERVICES else None

        # Set the request username to the service's username. If service request,
        # set as service username
        request.username = service_username or str(self.tapis_api_gateway.get_username())

        if request.username == None:
            return Unauthorized(f"Authentication Error")

        ### Auth end ###
        return super(RestrictedAPIView, self).dispatch(request, *args, **kwargs)

    # Takes a pydantic base model and tries to validate it.
    # If it fails, a BadRequest Response is returned with the error message
    # generated by pydantic
    def prepare(self, request_schema):
        try:
            request_object = request_schema(**self.request_body)
        except ValidationError as e:
            # NOTE : {'.'.join(error['loc'])} <-- Causes errors
            # errors = [ f"{str(error['type'])}. {str(error['msg'])}" for error in json.loads(e.json())]
            failure_view = BadRequest(message=str(e))

            self.prepared_request = PreparedRequest(is_valid=False, failure_view=failure_view)

            return self.prepared_request
        except Exception as e:
            failure_view = ServerError(str(e))

            self.prepared_request = PreparedRequest(is_valid=False, failure_view=failure_view)

        self.prepared_request = PreparedRequest(body=request_object)
        return self.prepared_request
        

