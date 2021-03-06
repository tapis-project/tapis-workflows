from pathlib import Path

BASE_DIR = str(Path(__file__).resolve().parent.parent) + "/"

STACK_FILE = BASE_DIR + "src/deployment/stack.json"

ENVS = [ "local", "dev", "staging", "prod" ]

DEPLOYMENT_TYPES = [ "docker", "kubernetes" ]