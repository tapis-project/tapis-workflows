import logging

from tapisservice import errors


def get_tenant_id_from_base_url(base_url, tenants):
    """
    Return the tenant_id associated with the base URL of a request.
    """
    if base_url and 'http://testserver' in base_url:
        logging.debug("http://testserver in url; resolving tenant id to dev for Django testing.")
        return 'dev'
    if base_url and 'http://localhost:500' in base_url:
        logging.debug("http://localhost:500 in url; resolving tenant id to tacc for user testing.")
        return 'tacc'

    request_tenant = tenants.get_tenant_config(url=base_url)
    return request_tenant.tenant_id

def resolve_tapis_v3_token(request, tenant_id, client):
    """
    Validates a tapis v3 token in the X-Tapis-Token header
    """
    v3_token = request.META.get('HTTP_X_TAPIS_TOKEN')
    if v3_token:
        try:
            claims = client.validate_token(v3_token)
        except errors.NoTokenError as e:
            msg = "No Tapis token found in the request. Be sure to specify the X-Tapis-Token header."
            logging.info(msg)
            return None, HttpResponseForbidden(make_error(msg=msg))
        except errors.AuthenticationError as e:
            msg = f"Tapis token validation failed; details: {e}"
            logging.info(msg)
            return None, HttpResponseForbidden(make_error(msg=msg))
        except Exception as e:
            msg = f"Unable to validate the Tapis token; details: {e}"
            logging.info(msg)
            return None, HttpResponseForbidden(make_error(msg=msg))

        # validate that the tenant claim matches the computed tenant_id
        # NOTE -- this does not work for service tokens; for those, have to check the OBO header.
        token_tenant = claims.get('tapis/tenant_id')
        if not token_tenant == tenant_id:
            msg = f"Unauthorized; the tenant claim in the token ({token_tenant}) did not match the associated " \
                  f"tenant in the request ({tenant_id})."
            return None, HttpResponseForbidden(make_error(msg=msg))
        return claims['tapis/username'], None
    else:
        msg = "No Tapis token found."
    return None, HttpResponseForbidden(make_error(msg=msg))