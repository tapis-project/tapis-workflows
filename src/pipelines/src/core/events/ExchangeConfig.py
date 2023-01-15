from typing import List, Union
from core.events.types import (
    PIPELINE_COMPLETED,
    PIPELINE_TERMINATED,
    PIPELINE_FAILED
)


class ExchangeConfig:
    def __init__(
        self,
        once: List[str] = [PIPELINE_COMPLETED, PIPELINE_FAILED, PIPELINE_TERMINATED], # TODO Maybe remove terminated
        reset_on: List[Union[str, int]] = [PIPELINE_COMPLETED, PIPELINE_FAILED, PIPELINE_TERMINATED]
    ):
        self.reset_on = [*reset_on]
        self.allow_once = [*once]