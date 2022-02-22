# TAPIS_TENANT = os.environ["TAPIS_TENANT"]
TAPIS_TENANT = "dev" # TODO

# TAPIS_SERVICE_ACCOUNT = os.environ["TAPIS_SERVICE_ACCOUNT"]
TAPIS_SERVICE_ACCOUNT = "testuser2" # TODO remove
TAPIS_SERVICE_ACCOUNT_PASSWORD = "testuser2"

TAPIS_BASE_URL = f"https://{TAPIS_TENANT}.tapis.io"

TAPIS_TOKEN_HEADER = "X-TAPIS-TOKEN"

DJANGO_TAPIS_TOKEN_HEADER = f"HTTP_{TAPIS_TOKEN_HEADER.replace('-', '_')}"

DIRECTIVE_DELIMITER = "|"
SUPPORTED_DIRECTIVES = [
    "BUILD", # Tells the Pipelines Service to run the build action if auto_build is False
    "DEPLOY", # Implies the BUILD directive. Tells the Pipelines Service to run any post_build actions
    "CACHE", # Tells the image builder whether or not the image layers should be cached.
    "CUSTOM_TAG", # A key-value pair. Uses the value specified in the directive as the image tage
    "COMMIT_CONTEXT", # TODO Document this
    "COMMIT_DESTINATION",
    "DRY_RUN", # Prevents an image and the subsequent actions from running
    "NO_PUSH", # Prevents the image builder from pushing the new image to the registry
]

DIRECTIVE_SET_PATTERN = r"(?<=[\[]{1})[a-zA-Z0-9\s:|._-]+(?=[\]]{1})"
DIRECTIVE_KEY_VAL_DELIMITER = ":"

PERMITTED_HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

PERMITTED_CONTENT_TYPES = ["application/json"]