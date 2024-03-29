from typing import List


class TaskResult:
    def __init__(
            self,
            status: int,
            output: dict={},
            errors: List[str]=[]
        ):
        self.errors = errors
        self.success = True if status == 0 else False
        self.skipped = False if status >= 0 else True
        self.status = status
        self.output = output