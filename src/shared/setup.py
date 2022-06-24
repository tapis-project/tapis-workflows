"""Pulls in the code from the shared/ directory"""

import shutil, os, json

from conf.configs import (
    BASE_DIR,
    TAPIS_SERVICE_ACCOUNT,
    TAPIS_SERVICE_ACCOUNT_PASSWORD,
    TAPIS_SERVICE_SITE_ID,
    TAPIS_SERVICE_TENANT_ID,
    WORKFLOWS_SERVICE_URL,
    LOG_LEVEL
)


SHARED_DIR = os.path.join(BASE_DIR, "/shared/")

# Load the config and rewrite it with the values from the env vars
shared_config_file_path = os.path.join(SHARED_DIR, "conf/config.json")
with open(shared_config_file_path, "r") as file:
    config = json.load(file)

config = {
    **config,
    "primary_site_admin_tenant_base_url": WORKFLOWS_SERVICE_URL,
    "log_level": LOG_LEVEL,
    "service_name": TAPIS_SERVICE_ACCOUNT,
    "service_password": TAPIS_SERVICE_ACCOUNT_PASSWORD,
    "service_site_id": TAPIS_SERVICE_SITE_ID,
    "service_tenant_id": TAPIS_SERVICE_TENANT_ID,
    "python_framework_type": "django", # Not django, but tapisservice requires something
    "tenants": []
}
config_file_path = os.path.join(BASE_DIR, "config.json")
with open(config_file_path, 'w') as file:
    json.dump(config, file)

# Copy the config file 
shared_configschema_file_path = os.path.join(SHARED_DIR, "conf/configschema.json")
configschema_file_path = os.path.join(SHARED_DIR, "conf/configschema.json")
shutil.copy(shared_configschema_file_path, configschema_file_path)

