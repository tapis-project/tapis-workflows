from typing import List


class TaskResult:
    def __init__(
            self,
            status: int,
            output: dict={},
            errors: List[str]=[],
            stdout: str=None,
            stderr: str=None
        ):
        self.errors = errors
        self.success = True if status == 0 else False
        self.status = status
        self.output = output
        self.stdout = stdout
        self.stderr = stderr