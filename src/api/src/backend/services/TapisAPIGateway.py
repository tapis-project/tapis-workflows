from tapipy.tapis import Tapis

from backend.conf.constants import TAPIS_BASE_URL


AUTH_METHODS = [
    "password",
    "jwt"
]

DEFAULT_AUTH_METHOD = "password"

class TapisAPIGateway:
    def __init__(self):
        self.base_url = TAPIS_BASE_URL
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

    def get_client(self):
        return self.client

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
            self.client = Tapis(
                base_url=self.base_url,
                jwt=credentials["jwt"]
            )

            self.username = str(self.client.authenticator.get_userinfo().username)

            return True

        except Exception as e:
            self.error = str(e)
            return False

service = TapisAPIGateway()