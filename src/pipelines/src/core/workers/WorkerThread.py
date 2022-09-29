from threading import Thread


class WorkerThread(Thread):
    def __init__(self, *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self.stopped = False