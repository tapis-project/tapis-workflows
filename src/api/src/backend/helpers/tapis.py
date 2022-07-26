import logging

from tapisservice import errors

from backend.utils import one_in
from backend.errors.api import AuthenticationError
from backend.services.TapisServiceAPIGateway import TapisServiceAPIGateway
from backend.conf.constants import LOCAL_DEV_URLS


service_client = TapisServiceAPIGateway().get_client()

def resolve_tenant_id(base_url):
    """
    Returns the tenant_id associated with the base url of a request.
    """
    if one_in(LOCAL_DEV_URLS, base_url):
        logging.debug("Resolving tenant id to 'dev' for local testing.")
        return "dev"

    tenants = service_client.tenant_cache
    tenant = tenants.get_tenant_config(url=base_url)

    return tenant.tenant_id

def resolve_tapis_v3_token(token, tenant_id):
    try:
        claims = service_client.validate_token(token)
    except errors.AuthenticationError as e:
        raise AuthenticationError(f"Tapis token validation failed; details: {e}")
    except Exception as e:
        raise AuthenticationError(f"Unable to validate the Tapis token; details: {e}")

    # validate that the tenant claim matches the computed tenant_id
    # NOTE -- this does not work for service tokens; for those, have to check the OBO header.
    token_tenant = claims.get('tapis/tenant_id')
    if not token_tenant == tenant_id:
        raise AuthenticationError(f"Unauthorized; the tenant claim in the token ({token_tenant}) did not match the associated tenant in the request ({tenant_id}).")
    
    return claims['tapis/username']