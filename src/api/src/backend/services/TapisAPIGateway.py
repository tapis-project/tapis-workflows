from tapipy.tapis import Tapis

from backend.conf.constants import TAPIS_DEV_URL, TAPIS_DEV_TENANT
from backend.helpers.tapis import resolve_tenant_id, resolve_tapis_v3_token
from backend.errors.api import AuthenticationError


AUTH_METHODS = [
    "password",
    "jwt"
]

DEFAULT_AUTH_METHOD = "password"

class TapisAPIGateway:
    def __init__(self, base_url):
        # Use the base url to determine the tenant
        self.tenant_id = resolve_tenant_id(base_url)
        
        # Set the base url to the tenant dev url if in the
        # dev tenant
        if self.tenant_id == TAPIS_DEV_TENANT:
            base_url = TAPIS_DEV_URL

        self.base_url = base_url
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

    def get_tenant_id(self):
        return self.tenant_id

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

            self.username = resolve_tapis_v3_token(
                credentials["jwt"],
                self.tenant_id
            )

        except AuthenticationError as e:
            self.error = str(e)
            return False
        except Exception as e:
            self.error = str(e)
            return False
        
        return True