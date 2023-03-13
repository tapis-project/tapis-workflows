from functools import partial
from logging import Logger
from typing import List


def log(funcs, *args, **kwargs):
    for func in funcs:
        func(*args, **kwargs)

class CompositeLogger:
    """Handles logs for both the application and pipeline runs"""
    def __init__(self, loggers: List[Logger]):
        self._loggers = loggers
        
    def __getattr__(self, __name):
        funcs = []
        for logger in self._loggers:
            funcs.append(getattr(logger, __name))

        return partial(log, funcs)