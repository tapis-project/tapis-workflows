class ActionResult:
    def __init__(self, status, data={}):
        self.success = True if status == 0 else False
        self.status = status
        self.data = data