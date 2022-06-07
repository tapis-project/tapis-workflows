from asyncio.events import BaseDefaultEventLoopPolicy
import os

from pathlib import Path


BASE_DIR = str(Path(__file__).resolve().parent.parent) + "/"

MAX_CONNECTION_ATTEMPTS = 24
RETRY_DELAY = 5

BASE_WORK_DIR = "/mnt/pipelines/"

LOG_FILE = BASE_DIR + "logs/service.log"

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

BROKER_URL = f"amqp://{BROKER_USER}:{BROKER_PASSWORD}@{BROKER_HOST}:{BROKER_PORT}"
BACKEND_URL = f"db+mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Read the kubernetes namespace from the serviceaccount namespace directly
KUBERNETES_NAMESPACE = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()

# Default polling interval in seconds
DEFAULT_POLLING_INTERVAL = 1

TAPIS_SERVICE_ACCOUNT = os.environ["WORKFLOWS_SERVICE_ACCOUNT"]
TAPIS_SERVICE_ACCOUNT_PASSWORD = os.environ["WORKFLOWS_SERVICE_PASSWORD"]

TAPIS_BASE_URL = "dev.tapis.io"
WORKFLOWS_SERVICE_URL = os.environ["WORKFLOWS_SERVICE_URL"]

TAPIS_JOB_POLLING_FREQUENCY = 2  # in seconds
