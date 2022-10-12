import uuid


class Worker:
    def __init__(self, _id=None):
        self.can_start = False
        self.id = _id if _id != None else uuid.uuid4()

    def __repr__(self):
        return f"{self.__class__.__name__} id: {self.id}"