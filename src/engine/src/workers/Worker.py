import uuid


class Worker:
    def __init__(self, _id=None):
        self.can_start = False

        # Unique identifier for this worker
        self.id = _id if _id != None else uuid.uuid4()

        # An array of all pipeline runs handled by this worker
        self.runs = []

        # The pipeline run currently being processed by this worker
        self.current_run = None

    def __repr__(self):
        return f"{self.__class__.__name__} id: {self.id}"
        