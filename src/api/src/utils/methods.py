def methods(cls):
    return [ method for method in dir(cls) if (
        (not method.startswith("__"))
        and callable(getattr(cls, method))
    )]