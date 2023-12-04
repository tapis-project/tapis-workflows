from collections import deque
from threading import Lock

from errors import WorkerLimitExceed, NoAvailableWorkers
from core.server import Worker


class WorkerPool:
    def __init__(
        self,
        worker_cls: Worker,
        starting_worker_count,
        max_workers=1000,
        worker_args=[],
        worker_kwargs={},
    ):
        self.max_workers = max_workers
        # Double-ended queue. Like a list but better
        self.pool = deque()

        # Generate the workers
        self.worker_cls = worker_cls
        for i in range(starting_worker_count):
            self.pool.append(worker_cls(*worker_args, _id=i, **worker_kwargs))
            
        self.checked_out = []
        
        # Pessimistic locking mechanism
        self.lock = Lock()

    def check_out(self):
        # To prevent other threads from checking out the same worker more than
        # once, we lock it down using the threading.Lock thread locker
        self.lock.acquire()
        
        # Return a worker if one or more in the pool
        if len(self.pool) > 0:
            worker = self.pool.pop()
            self.checked_out.append(worker)
            # Release the lock
            self.lock.release()
            return worker

        # Calculate the total number of workers
        total_workers = len(self.checked_out) + len(self.pool)

        # Create a new worker if there are no available workers and the 
        # max worker limit has not yet been reached
        if total_workers < self.max_workers:
            worker = self.worker_cls()
            self.checked_out.append(worker)
            # Release the lock
            self.lock.release()
            return worker

        # Release the lock
        self.lock.release()

        # There are no more available workers
        raise NoAvailableWorkers(f"No available workers: Max Workers: {self.max_workers}")

    def check_in(self, worker):
        if worker in self.checked_out:
            self.checked_out.remove(worker)
        
        self.pool.appendleft(worker)
        
        if self.count() > self.max_workers:
            self.pool.remove(worker)
            raise WorkerLimitExceed(f"This WorkerPool has exceed the maximum allowable number of workers ({self.max_workers})")

    def count(self):
        return len(self.checked_out) + len(self.pool)

    def get_all_running(self):
        return self.checked_out
        



        
        
