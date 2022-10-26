import os

from pathlib import Path

from core.tasks.Flavor import Flavor


BASE_DIR = str(Path(__file__).resolve().parent.parent) + "/"

# PipelineExecutor configs
MAX_CONNECTION_ATTEMPTS = 24
CONNECTION_RETRY_DELAY = 5

INSUFFICIENT_WORKER_RETRY_DELAY = 10

STARTING_WORKERS = 2
MAX_WORKERS = 2

# Exchanges
INBOUND_EXCHANGE = "workflows"
RETRY_EXCHANGE = "retry"
DEAD_LETTER_EXCHANGE = "deadletter"

# Queues
INBOUND_QUEUE = "workflows"
RETRY_QUEUE = "retry"
DEAD_LETTER_QUEUE = "deadletter"

BASE_WORK_DIR = "/mnt/pipelines/"

LOG_FILE = BASE_DIR + "logs/service.log"

LOG_LEVEL = os.environ["LOG_LEVEL"]

# TODO probably remove. Going full kubernetes
DEPLOYMENT_TYPE = os.environ["DEPLOYMENT_TYPE"]

WORKFLOWS_API_BASE_URL = os.environ["WORKFLOWS_API_BASE_URL"]

BROKER_USER = os.environ["BROKER_USER"]
BROKER_PASSWORD = os.environ["BROKER_PASSWORD"]
BROKER_HOST = os.environ["BROKER_URL"]
BROKER_PORT = os.environ["BROKER_PORT"]

DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]

LOG_LEVEL = os.environ["LOG_LEVEL"]

BROKER_URL = f"amqp://{BROKER_USER}:{BROKER_PASSWORD}@{BROKER_HOST}:{BROKER_PORT}"
BACKEND_URL = f"db+mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Read the kubernetes namespace from the serviceaccount namespace directly
KUBERNETES_NAMESPACE = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()

# TODO PIPELINES_PVC = os.environ["WORKFLOWS_PIPELINES_PVC"]
PIPELINES_PVC = "workflows-pipelines-pvc"

# Polling intervals in seconds
DEFAULT_POLLING_INTERVAL = 1
MIN_POLLING_INTERVAL = 1
MAX_POLLING_INTERVAL = 3600

# Duplicate submission policy enums
DUPLICATE_SUBMISSION_POLICY_TERMINATE = "terminate"
DUPLICATE_SUBMISSION_POLICY_ALLOW = "allow"
DUPLICATE_SUBMISSION_POLICY_DENY = "deny"

# Execution profile
DEFAULT_MAX_EXEC_TIME = 86400 # 1 day TODO Consider higher
DEFAULT_INVOCATION_MODE = "async"
DEFAULT_RETRY_POLICY = "exponential_backoff"
DEFAULT_DUPLICATE_SUBMISSION_POLICY = "terminate"
DEFAULT_MAX_RETRIES = 0

# Image tags and urls
KANIKO_IMAGE_URL = "gcr.io/kaniko-project/executor"
KANIKO_IMAGE_TAG = "debug"

# Container Flavors - Image Builders
FLAVOR_B1_LARGE = Flavor(cpu="4", memory="4G", disk="0")
FLAVOR_B1_XLARGE = Flavor(cpu="4", memory="8G", disk="0")
FLAVOR_B1_XXLARGE = Flavor(cpu="4", memory="16G", disk="0")

# Container Flavors - Compute
FLAVOR_C1_SMALL = Flavor(cpu="1", memory="1G", disk="20GB")
FLAVOR_C1_MEDIUM = Flavor(cpu="2", memory="2G", disk="20GB")
FLAVOR_C1_LARGE = Flavor(cpu="4", memory="4G", disk="20GB")
FLAVOR_C1_XLARGE = Flavor(cpu="8", memory="8G", disk="20GB")
FLAVOR_C1_XXLARGE = Flavor(cpu="16", memory="16G", disk="20GB")

FLAVORS = [
    FLAVOR_B1_LARGE, FLAVOR_B1_XLARGE, FLAVOR_B1_XLARGE,
    FLAVOR_C1_SMALL, FLAVOR_C1_MEDIUM, FLAVOR_C1_LARGE, FLAVOR_C1_XLARGE, FLAVOR_C1_XXLARGE,
]

SINGULARITY_IMAGE_URL = "quay.io/singularity/singularity"
SINGULARITY_IMAGE_TAG = "v3.10.0"

TAPIS_SERVICE_ACCOUNT = os.environ["WORKFLOWS_SERVICE_ACCOUNT"]
TAPIS_SERVICE_ACCOUNT_PASSWORD = os.environ["WORKFLOWS_SERVICE_PASSWORD"]
TAPIS_SERVICE_SITE_ID = os.environ["TAPIS_SERVICE_SITE_ID"]
TAPIS_SERVICE_TENANT_ID = os.environ["TAPIS_SERVICE_TENANT_ID"]
TAPIS_SERVICE_LOG_FILE = "/src/logs/workflows.logs"

TAPIS_DEV_URL = os.environ["TAPIS_DEV_URL"]
WORKFLOWS_SERVICE_URL = os.environ["WORKFLOWS_SERVICE_URL"]

TAPIS_JOB_POLLING_FREQUENCY = 2  # in seconds
