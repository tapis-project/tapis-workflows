import uuid

from core.workers import WorkerThread


class Worker:
    def __init__(self, _id=None):
        self.can_start = False
        self.id = _id if _id != None else uuid.uuid4()

    def start(self, target, ctx, worker):
        self.thread = WorkerThread(
            target=target,
            args=(ctx, worker)
        )
        self.thread.start()