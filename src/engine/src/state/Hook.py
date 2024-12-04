def method_hook(fn):
    def wrapper(self, *args, **kwargs):
        return fn(self, *args, **kwargs)

    return wrapper

class Hook:
    def __init__(
        self,
        fn: callable,
        args: tuple=tuple(),
        kwargs: dict={},
        attrs: list[str]=[]
    ):
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.attrs = attrs

    def __call__(self, state):
        return self._fn(state, *self._args, **self._kwargs)


# class Hook:
#     def __init__(self, fn: callable, attrs: List[str]):
#         self.fn = fn
#         self.attrs = attrs

#     def __call__(self, state):
#         return self.fn(state)