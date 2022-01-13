from pathlib import Path


BASE_DIR = str(Path(__file__).resolve().parent.parent) + "/"

MAX_CONNECTION_ATTEMPTS = 24
RETRY_DELAY = 5

BASE_KANIKO_FILE = BASE_DIR + "conf/kaniko-base.yml"
WORK_DIR = BASE_DIR + "work/"