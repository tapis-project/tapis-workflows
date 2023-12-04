import copy

from typing import Any
from threading import Lock


class ReactiveState(object):
    """ReactiveState is a thread-safe state management mechanism that allows
    user-defined functions to be performed when when state is queried or mutated.
    
    NOTE This will only work when the object's attributes are fetched and set directly,
    and refrences created to this object will not 
    """

    def __init__(
        self,
        hooks,
        initial_state={},
        lock=Lock()
    ):
        super(ReactiveState, self).__setattr__("_hooks", hooks)
        super(ReactiveState, self).__setattr__("_lock", lock)
        super(ReactiveState, self).__setattr__("_called_externally", True)
        super(ReactiveState, self).__setattr__("_initial_state", initial_state)
        super(ReactiveState, self).__setattr__("_state", copy.deepcopy(initial_state))
        
    def __setattr__(self, __name: str, __value: Any) -> None:
        if self._called_externally:
            self._set_external(__name, __value)
            return

        self._set_internal(__name, __value)

    def __getattr__(self, __name: str) -> Any:
        if self._called_externally:
            return self._get_external(__name)

        return self._get_internal(__name)

    def _set_external(self, __name: str, __value: Any) -> None:
        self._lock.acquire()

        self._state[__name] = __value

        try:
            self._run_hooks(__name)
        except Exception as e:
            self._lock.release()
            raise e

        self._lock.release()

    def _set_internal(self, __name: str, __value: Any) -> None:
        self._state[__name] = __value

    def _get_external(self, __name: str) -> None:
        self._lock.acquire()

        try:
            value = self._state[__name]
        except KeyError:
            self._lock.release()
            raise AttributeError(f"type object '{type(self)}' has no attribute '{__name}'")

        try:
            self._run_hooks(__name)
        except Exception as e:
            self._lock.release()
            raise e
        
        self._lock.release()

        return value
    
    def _get_internal(self, __name: str) -> None:
        try:
            value = self._state[__name]
        except KeyError:
            self._lock.release()
            raise AttributeError(f"type object '{type(self)}' has no attribute '{__name}'")

        return value

    def _run_hooks(self, __name):
        super(ReactiveState, self).__setattr__("_called_externally", False)
        for hook in self._hooks:
            if __name in hook.attrs or len(hook.attrs) == 0:
                hook(self)
        super(ReactiveState, self).__setattr__("_called_externally", True)

    def reset(self):
        super(ReactiveState, self).__setattr__("_state", copy.deepcopy(self._initial_state))