import os

SECRETS_TENANT = "admin"

WORKFLOWS_SERVICE_ACCOUNT = os.environ["WORKFLOWS_SERVICE_ACCOUNT"]
WORKFLOWS_SERVICE_PASSWORD = os.environ["WORKFLOWS_SERVICE_PASSWORD"]

TAPIS_DEV_URL = os.environ["TAPIS_DEV_URL"]
TAPIS_DEV_TENANT = "dev" # TODO add to environment variables
LOCAL_DEV_HOSTS = ["127.0.0.1", "localhost", "c006.rodeo.tacc.utexas.edu"]

TAPIS_SERVICE_SITE_ID = os.environ["TAPIS_SERVICE_SITE_ID"]
TAPIS_SERVICE_TENANT_ID = os.environ["TAPIS_SERVICE_TENANT_ID"]
TAPIS_SERVICE_ACCOUNT = WORKFLOWS_SERVICE_ACCOUNT
TAPIS_SERVICE_ACCOUNT_PASSWORD = WORKFLOWS_SERVICE_PASSWORD
WORKFLOWS_SERVICE_URL = os.environ["WORKFLOWS_SERVICE_URL"]
TAPIS_SERVICE_LOG_FILE = "/src/logs/workflows.logs"

LOG_LEVEL = os.environ["LOG_LEVEL"]

TAPIS_TOKEN_HEADER = "X-TAPIS-TOKEN"

DJANGO_TAPIS_TOKEN_HEADER = f"HTTP_{TAPIS_TOKEN_HEADER.replace('-', '_')}"

DIRECTIVE_DELIMITER = "|"
SUPPORTED_DIRECTIVES = [
    "DEPLOY", # Implies the BUILD directive. Tells the Pipelines Service to run any post_build tasks
    "CACHE", # Tells the image builder whether or not the image layers should be cached.
    "CUSTOM_TAG", # A key-value pair. Uses the value specified in the directive as the image tag
    "TAG_COMMIT_SHA", # Tells the image builder to tag the image with the commit_sha if one exists
    "DRY_RUN", # Simulates a pipeline run without triggering task executors
    "NO_PUSH", # Prevents the image builder from pushing the new image to the registry
]

DIRECTIVE_SET_PATTERN = r"(?<=[\[]{1})[a-zA-Z0-9\s:|._-]+(?=[\]]{1})"
DIRECTIVE_KEY_VAL_DELIMITER = ":"

PERMITTED_HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

PERMITTED_CONTENT_TYPES = ["application/json"]