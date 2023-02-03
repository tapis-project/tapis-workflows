from utils.Styles import styler


class WorkflowsBaseException(Exception):
    def __init__(self, message, hint=""):
        self.message = message
        self.hint = hint

    def __str__(self):
        message = self.message
        if self.hint != "":
            hint = f"{styler.warn('HINT')}: {self.hint}"
            message = f"{message}\n{hint})"
        return f"{styler.danger(self.__class__.__name__)}: {message}"
