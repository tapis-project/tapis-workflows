from typing import List, Union
from core.events.types import PIPELINE_COMPLETED, PIPELINE_TERMINATED


class ExchangeConfig:
    def __init__(
        self,
        reset_on: List[Union[str, int]] = [PIPELINE_COMPLETED, PIPELINE_TERMINATED]
    ):
        self.reset_on=[reset_on]