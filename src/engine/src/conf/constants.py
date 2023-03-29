import os

from pathlib import Path

from core.tasks.Flavor import Flavor


BASE_DIR = str(Path(__file__).resolve().parent.parent) + "/"
OWE_PYTHON_SDK_DIR = os.path.join(BASE_DIR, "owe-python-sdk")

IS_LOCAL = True if os.environ.get("IS_LOCAL", 'false') == 'true' else False

# PipelineExecutor configs
MAX_CONNECTION_ATTEMPTS = 24
CONNECTION_RETRY_DELAY = 5

INSUFFICIENT_WORKER_RETRY_DELAY = 10

STARTING_WORKERS = os.environ.get("MIN_WORKERS", None) or 2
MAX_WORKERS = os.environ.get("MAX_WORKERS", None) or 10

# Exchanges
INBOUND_EXCHANGE = "workflows"
RETRY_EXCHANGE = "retry"
DEAD_LETTER_EXCHANGE = "deadletter"
DEFERRED_EXCHANGE = "deferred"

# Queues
INBOUND_QUEUE = "workflows"
RETRY_QUEUE = "retry"
DEAD_LETTER_QUEUE = "deadletter"
DEFERRED_QUEUE = "deferred"

BASE_WORK_DIR = "/mnt/pipelines/"

LOG_FILE = BASE_DIR + "logs/service.log"

LOG_LEVEL = os.environ["LOG_LEVEL"]

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

WORKFLOW_NFS_SERVER = os.environ.get("WORKFLOW_NFS_SERVER")

# Polling intervals in seconds
DEFAULT_POLLING_INTERVAL = 1
MIN_POLLING_INTERVAL = 1
MAX_POLLING_INTERVAL = 3600

# Duplicate submission policy enums
DUPLICATE_SUBMISSION_POLICY_TERMINATE = "terminate"
DUPLICATE_SUBMISSION_POLICY_ALLOW = "allow"
DUPLICATE_SUBMISSION_POLICY_DENY = "deny"
DUPLICATE_SUBMISSION_POLICY_DEFER = "defer"

# Execution profile
DEFAULT_MAX_EXEC_TIME = 60 * 60 * 24
DEFAULT_INVOCATION_MODE = "async"
DEFAULT_RETRY_POLICY = "exponential_backoff"
DEFAULT_DUPLICATE_SUBMISSION_POLICY = "terminate"
DEFAULT_MAX_RETRIES = 0

# Image tags and urls
KANIKO_IMAGE_URL = "gcr.io/kaniko-project/executor"
KANIKO_IMAGE_TAG = "debug"

# Container Flavors - Image Builders
FLAVOR_B1_LARGE = Flavor(cpu="4", memory="4G", disk="20GB")
FLAVOR_B1_XLARGE = Flavor(cpu="4", memory="8G", disk="20GB")
FLAVOR_B1_XXLARGE = Flavor(cpu="4", memory="16G", disk="20GB")

# Container Flavors - Compute
FLAVOR_C1_SMALL = Flavor(cpu="1", memory="1G", disk="20GB")
FLAVOR_C1_MEDIUM = Flavor(cpu="2", memory="2G", disk="20GB")
FLAVOR_C1_LARGE = Flavor(cpu="4", memory="4G", disk="20GB")
FLAVOR_C1_XLARGE = Flavor(cpu="8", memory="8G", disk="20GB")
FLAVOR_C1_XXLARGE = Flavor(cpu="16", memory="16G", disk="20GB")

FLAVORS = [
    FLAVOR_B1_LARGE, FLAVOR_B1_XLARGE, FLAVOR_B1_XXLARGE,
    FLAVOR_C1_SMALL, FLAVOR_C1_MEDIUM, FLAVOR_C1_LARGE, FLAVOR_C1_XLARGE, FLAVOR_C1_XXLARGE,
]

SINGULARITY_IMAGE_URL = "quay.io/singularity/singularity"
SINGULARITY_IMAGE_TAG = "v3.10.0"
