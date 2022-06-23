import logging

from tapisservice.tenants import TenantCache
from tapisservice.auth import get_service_tapis_client  


class TapisServiceGateway:
    def __init__(self):
        try:
            self.client = get_service_tapis_client(tenants=TenantCache())
        except Exception as e:
            logging.error(f'Could not instantiate tapisservice client. Exception: {e}')
            raise e

    def get_client(self):
        return self.client