import json

from types import SimpleNamespace

from conf.configs import STACK_FILE


class BaseDeployer:
    def __init__(self):
        # Load JSON object and convert to a python object
        # so we can access properties using dot notation
        self.components = json.loads(
            open(STACK_FILE, "r").read(),
            object_hook=lambda d: SimpleNamespace(**d)
        ).Components