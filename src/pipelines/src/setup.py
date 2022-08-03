import json, os

from conf.configs import (
    TAPIS_SERVICE_ACCOUNT,
    TAPIS_SERVICE_ACCOUNT_PASSWORD,
    TAPIS_SERVICE_SITE_ID,
    TAPIS_SERVICE_TENANT_ID,
    WORKFLOWS_SERVICE_URL,
    TAPIS_SERVICE_LOG_FILE
)

def setup():
    # Load the config and rewrite it with the values from the env vars
    with open("config.json", "r") as file:
        config = json.load(file)

    config = {
        **config,
        "primary_site_admin_tenant_base_url": WORKFLOWS_SERVICE_URL,
        "log_level": "ERROR",
        "service_name": TAPIS_SERVICE_ACCOUNT,
        "service_password": TAPIS_SERVICE_ACCOUNT_PASSWORD,
        "service_site_id": TAPIS_SERVICE_SITE_ID,
        "service_tenant_id": TAPIS_SERVICE_TENANT_ID,
        "python_framework_type": "django", # Not django, but tapisservice requires something
        "log_file": TAPIS_SERVICE_LOG_FILE,
        # "tapisservice.auth_log_file": os.devnull,
        # "tapisservice.log_log_file": os.devnull,
        "tenants": []
    }

    with open("config.json", 'w') as file:
        json.dump(config, file)

setup()