from state import ReactiveState


class WorkflowExecutorStateDAO:
    def __init__(self, state: ReactiveState):
        self._state = state

    def get_state(self):
        return self._state
