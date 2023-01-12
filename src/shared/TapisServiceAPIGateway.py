import logging

from tapisservice.auth import get_service_tapis_client  
from tapisservice.tenants import TenantCache


class TapisServiceAPIGateway:
    def __init__(self,
        tenants=TenantCache(),
        jwt=None
    ):  
        kwargs = {}
        if jwt != None:
            kwargs.update({"jwt": jwt})
        elif jwt == None:
            kwargs.update({"tenants": tenants})
        
        self.client = None
        try:
            self.client = get_service_tapis_client(**kwargs)
        except Exception as e:
            logging.error(f'Could not instantiate tapisservice client. Exception: {e}')

    def get_client(self):
        return self.client