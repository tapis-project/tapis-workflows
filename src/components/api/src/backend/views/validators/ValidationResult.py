class ValidationResult:
    def __init__(
        self,
        success=True,
        body=None,
        message=None,
        failure_view=None
    ):
        self.success = success
        self.body = body
        self.message = message
        self.failure_view = failure_view