import os

from tapipy.tapis import Tapis
from tapipy.errors import BaseTapyException

from backend.services.UserService import user_service

AUTH_METHODS = [
    "password",
    "jwt"
]

DEFAULT_AUTH_METHOD = "password"


class TapisAuthenticator:
    def __init__(self):
        tenant = os.environ["TAPIS_TENANT"]
        self.base_url = f"https://{tenant}.tapis.io"
        self.client = None
        self.credentials = {}
        self.error = None
        self.username = None

    def authenticate(
        self,
        credentials: dict,
        auth_method: str = DEFAULT_AUTH_METHOD
    ):
        fn = getattr(self, f"_{auth_method}")
        
        return fn(credentials)

    def get_jwt(self):
        return self.client.get_access_jwt()

    def get_username(self):
        return self.username

    def _password(self, credentials):
        try:
            self.client = Tapis(
                base_url=self.base_url,
                username=credentials["username"],
                password=credentials["password"],
            )

            # Throws an error if the credentials are invalid
            self.client.get_tokens()
            
            return True

        except Exception as e:
            self.error = str(e)
            return False

    def _jwt(self, credentials):
        try:
            self.client=Tapis(
                base_url=self.base_url,
                jwt = credentials["jwt"]
            )

            self.username = str(self.client.authenticator.get_userinfo().username)

            return True

        except Exception as e:
            self.error = str(e)
            return False

authenticator = TapisAuthenticator()