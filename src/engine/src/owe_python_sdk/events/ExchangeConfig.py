from typing import List, Union
from owe_python_sdk.events.types import (
    PIPELINE_COMPLETED,
    PIPELINE_TERMINATED,
    PIPELINE_FAILED
)


class ExchangeConfig:
    def __init__(
        self,
        # The allow once list will permit handling of specific events only once
        # per subscriber
        allow_once: List[str] = [PIPELINE_COMPLETED, PIPELINE_FAILED, PIPELINE_TERMINATED], # TODO Maybe remove terminated
        reset_on: List[Union[str, int]] = [PIPELINE_COMPLETED, PIPELINE_FAILED, PIPELINE_TERMINATED]
    ):
        self.allow_once = [*allow_once]
        self.reset_on = [*reset_on]