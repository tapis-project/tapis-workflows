from typing import List


class ActionResult:
    def __init__(self, status: int, data: dict={}, errors: List[str]=[]):
        self.errors = errors
        self.success = True if status == 0 else False
        self.status = status
        self.data = data