import os

from pathlib import Path

from owe_python_sdk.schema import EnumTaskFlavor


class Configuration:
    def __init__(self):
        self.BASE_DIR = str(Path(__file__).resolve().parent.parent) + "/"
        self.OWE_PYTHON_SDK_DIR = os.path.join(self.BASE_DIR, "owe_python_sdk")

        self.IS_LOCAL = True if os.environ.get("IS_LOCAL", 'false') == 'true' else False

        # PipelineExecutor configs
        self.MAX_CONNECTION_ATTEMPTS = 24
        self.CONNECTION_RETRY_DELAY = 5

        self.INSUFFICIENT_WORKER_RETRY_DELAY = 10

        # STARTING_WORKERS = os.environ.get("MIN_WORKERS", None) or 2
        self.STARTING_WORKERS = 100
        # MAX_WORKERS = os.environ.get("MAX_WORKERS", None) or 10
        self.MAX_WORKERS = 200

        # Exchanges
        self.INBOUND_EXCHANGE = "workflows"
        self.RETRY_EXCHANGE = "retry"
        self.DEAD_LETTER_EXCHANGE = "deadletter"
        self.DEFERRED_EXCHANGE = "deferred"

        # Queues
        self.INBOUND_QUEUE = "workflows"
        self.RETRY_QUEUE = "retry"
        self.DEAD_LETTER_QUEUE = "deadletter"
        self.DEFERRED_QUEUE = "deferred"

        self.BASE_WORK_DIR = "/var/lib/open-workflow-engine/"

        self.LOG_FILE = self.BASE_DIR + "logs/service.log"

        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", None)

        self.BROKER_USER = os.environ.get("BROKER_USER", None)
        self.BROKER_PASSWORD = os.environ.get("BROKER_PASSWORD", None)
        self.BROKER_HOST = os.environ.get("BROKER_URL", None)
        self.BROKER_PORT = os.environ.get("BROKER_PORT", None)

        self.DB_USER = os.environ.get("DB_USER", None)
        self.DB_PASSWORD = os.environ.get("DB_PASSWORD", None)
        self.DB_HOST = os.environ.get("DB_HOST", None)
        self.DB_PORT = os.environ.get("DB_PORT", None)
        self.DB_NAME = os.environ.get("DB_NAME", None)

        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", None)

        self.BROKER_URL = f"amqp://{self.BROKER_USER}:{self.BROKER_PASSWORD}@{self.BROKER_HOST}:{self.BROKER_PORT}"
        self.BACKEND_URL = f"db+mysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

        # Read the kubernetes namespace from the serviceaccount namespace directly
        try:
            self.KUBERNETES_NAMESPACE = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()
        except Exception:
            pass
        finally:
            self.KUBERNETES_NAMESPACE = "default"

        self.WORKFLOW_NFS_SERVER = os.environ.get("WORKFLOW_NFS_SERVER")

        # Polling intervals in seconds
        self.DEFAULT_POLLING_INTERVAL = 1
        self.MIN_POLLING_INTERVAL = 1
        self.MAX_POLLING_INTERVAL = 3600

        # Duplicate submission policy enums
        self.DUPLICATE_SUBMISSION_POLICY_TERMINATE = "terminate"
        self.DUPLICATE_SUBMISSION_POLICY_ALLOW = "allow"
        self.DUPLICATE_SUBMISSION_POLICY_DENY = "deny"
        self.DUPLICATE_SUBMISSION_POLICY_DEFER = "defer"

        # Execution profile
        self.DEFAULT_MAX_EXEC_TIME = 60 * 60 * 24
        self.DEFAULT_INVOCATION_MODE = "async"
        self.DEFAULT_RETRY_POLICY = "exponential_backoff"
        self.DEFAULT_DUPLICATE_SUBMISSION_POLICY = "terminate"
        self.DEFAULT_MAX_RETRIES = 0

        # Image tags and urls
        self.KANIKO_IMAGE_URL = "gcr.io/kaniko-project/executor"
        # KANIKO_IMAGE_TAG = "debug"
        self.KANIKO_IMAGE_TAG = "latest"

        self.FLAVORS = {
            # EnumTaskFlavor.C1_XTINY: {"cpu": "1", "memory": ".01G", "disk": "1GB"},
            EnumTaskFlavor.C1_TINY: {"cpu": "1", "memory": ".5G", "disk": "20GB"},
            EnumTaskFlavor.C1_XXSML: {"cpu": "1", "memory": "1G", "disk": "20GB"},
            EnumTaskFlavor.C1_XSML: {"cpu": "1", "memory": "2G", "disk": "20GB"},
            EnumTaskFlavor.C1_SML: {"cpu": "1", "memory": "4G", "disk": "20GB"},
            EnumTaskFlavor.C1_MED: {"cpu": "2", "memory": "8G", "disk": "20GB"},
            EnumTaskFlavor.C1_LRG: {"cpu": "4", "memory": "16G", "disk": "20GB"},
            EnumTaskFlavor.C1_XLRG: {"cpu": "8", "memory": "32G", "disk": "20GB"},
            EnumTaskFlavor.C1_XXLRG: {"cpu": "16", "memory": "64G", "disk": "20GB"},
            EnumTaskFlavor.G1_NVD_SML: {"gpu": "1", "gpu_type": "nvidia.com/gpu", "memory": "4G", "disk": "20GB"},
            EnumTaskFlavor.G1_NVD_MED: {"gpu": "2", "gpu_type": "nvidia.com/gpu", "memory": "8G", "disk": "20GB"},
            EnumTaskFlavor.G1_NVD_LRG: {"gpu": "4", "gpu_type": "nvidia.com/gpu", "memory": "6G", "disk": "20GB"}
        }

        self.SINGULARITY_IMAGE_URL = "quay.io/singularity/singularity"
        self.SINGULARITY_IMAGE_TAG = "v3.10.0"

        self.PLUGINS = [ "contrib/tapis" ]