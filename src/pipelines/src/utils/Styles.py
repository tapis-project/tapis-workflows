class Styles:
    """ANSI escape codes"""

    DEBUG = "\033[95m"
    BLUE = "\033[94m"
    SUCCESS = "\033[92m"
    INFO = "\033[97m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    MUTED = "\033[90m"
    CYAN = "\033[36m"


class Styler:
    def apply(self, style, string):
        return style + string + Styles.RESET

    def underline(self, string):
        return self.apply(Styles.UNDERLINE, string)

    def bold(self, string):
        return self.apply(Styles.BOLD, string)

    def cyan(self, string):
        return self.apply(Styles.CYAN, string)

    def muted(self, string):
        return self.apply(Styles.MUTED, string)

    def danger(self, string):
        return self.apply(Styles.ERROR, string)

    def warn(self, string):
        return self.apply(Styles.WARNING, string)

    def info(self, string):
        return self.apply(Styles.INFO, string)


styler = Styler()
