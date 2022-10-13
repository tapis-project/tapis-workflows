import logging

from tapisservice.auth import get_service_tapis_client  
from tapisservice.tenants import TenantCache


class TapisServiceAPIGateway:
    def __init__(self):
        self.client = None
        try:
            self.client = get_service_tapis_client(
                tenants=TenantCache()
            )
        except Exception as e:
            logging.error(f'Could not instantiate tapisservice client. Exception: {e}')

    def get_client(self):
        return self.client