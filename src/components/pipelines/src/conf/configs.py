import os

from pathlib import Path


BASE_DIR = str(Path(__file__).resolve().parent.parent) + "/"

MAX_CONNECTION_ATTEMPTS = 24
RETRY_DELAY = 5

BASE_KANIKO_FILE = BASE_DIR + "conf/kaniko-base.yml"
SCRATCH_DIR = BASE_DIR + "scratch/"

DEPLOYMENT_TYPE = os.environ["DEPLOYMENT_TYPE"]

API_BASE_URL = os.environ["API_BASE_URL"]

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