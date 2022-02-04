import json

from django.contrib.auth.models import User

from backend.models import Account
from backend.views.APIView import APIView
from backend.services.Authenticator import authenticator
from backend.views.responses.BaseResponse import BaseResponse
from backend.views.responses.http_errors import Unauthorized, BadRequest
from utils.attrs import has_all_keys


class Accounts(APIView):
    def post(self, request):
        body = json.loads(request.body)

        if not has_all_keys(body, ["username", "password"]):
            return BadRequest()
        
        # Attempt to authenticate the user using their TACC username and
        # password
        authenticated = authenticator.authenticate(
            body, auth_method = "password")

        # Respond with 403 if authentication failed
        if not authenticated:
            return Unauthorized()

        # Create the user in the database
        user = User.objects.create_user(
            username=body["username"], password=body["password"])

        # Create an Account for the new user. The Account is an extension of
        # the User model (known as a profile model) that allows for custom
        # attributes 
        account = Account.object.create(user=user)
        

        return BaseResponse(message="successfully authenticated", data={
            "jwt": authenticator.get_jwt(),
            "account": account,
            "user": user
        })