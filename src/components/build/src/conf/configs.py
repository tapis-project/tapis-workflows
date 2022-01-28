import os

from pathlib import Path


BASE_DIR = str(Path(__file__).resolve().parent.parent) + "/"

MAX_CONNECTION_ATTEMPTS = 24
RETRY_DELAY = 5

BASE_KANIKO_FILE = BASE_DIR + "conf/kaniko-base.yml"
SCRATCH_DIR = BASE_DIR + "scratch/"

DEPLOYMENT_TYPE = os.environ["DEPLOYMENT_TYPE"]

API_BASE_URL = os.environ["API_BASE_URL"]