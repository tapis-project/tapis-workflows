from contrib.tapis.helpers.TapisServiceAPIGateway import TapisServiceAPIGateway
from tapipy.tapis import Tapis
import jwt;

def resolve_base_url_from_jwt(token: str):
    decoded = jwt.decode(token, options={"verify_signature": False})
    return decoded["iss"].removesuffix("")

def new_tapis_client(jwt: str) -> Tapis:
    client = Tapis(
        base_url=resolve_base_url_from_jwt(jwt),
        jwt=jwt
    )

    client.get_tokens()

    return client
