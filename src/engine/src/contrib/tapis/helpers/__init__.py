from contrib.tapis.helpers.TapisServiceAPIGateway import TapisServiceAPIGateway
from tapipy.tapis import Tapis
import jwt;

def resolve_base_url_from_jwt(token: str):
    # TODO The base url should NOT be derived from the token. it is possible
    # that the authenticator may be sitting an another site. Therefore, we
    # should proabably pass the base url through the args in the Workflows API
    decoded = jwt.decode(token, options={"verify_signature": False})
    return decoded["iss"].removesuffix("/v3/tokens")

def new_tapis_client(jwt: str) -> Tapis:
    client = Tapis(
        base_url=resolve_base_url_from_jwt(jwt),
        jwt=jwt
    )

    return client
