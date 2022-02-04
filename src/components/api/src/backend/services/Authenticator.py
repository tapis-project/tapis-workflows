import os

from tapipy.tapis import Tapis

from backend.services.UserService import user_service

GRANT_TYPES = [
    "password",
    "jwt"
]

DEFAULT_GRANT_TYPE = "password"


class TapisAuthenticator:
    def __init__(self):
        tenant = os.environ["TAPIS_TENANT"]
        self.base_url = f"https://{tenant}.tapis.io"
        self.jwt = None
        self.credentials = {}
        self.error = None

    def authenticate(
        self,
        credentials: dict,
        grant_type: str = DEFAULT_GRANT_TYPE
    ):
        auth_fn = getattr(self, f"_{grant_type}")
        
        return auth_fn(credentials)

    def get_jwt(self):
        return self.jwt

    def _password(self, credentials):
        try:
            client = Tapis(
                base_url = self.base_url,
                username = credentials["username"],
                password = credentials["password"],
            )

            client.get_tokens()

            self.jwt = client.access_token.access_token
            
            return True

        except Exception as e:
            self.error = e
            return False

    def _jwt(self, credentials):
        try:
            client = Tapis(
                base_url = self.base_url,
                jwt = credentials["jwt"]
            )

            client.get_tokens()

            self.jwt = client.access_token.access_token

            return True

        except Exception as e:
            self.error = e
            return False

authenticator = TapisAuthenticator()