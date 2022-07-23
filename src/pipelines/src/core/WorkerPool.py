from collections import deque

from errors.workers import WorkerLimitExceed


class WorkerPool:
    def __init__(self, worker_cls, starting_worker_count, max_workers=1):
        self.max_workers = max_workers
        # Double-ended queue. Like a list but better
        self.pool = deque()

        # Generate the workers
        self.worker_cls = worker_cls
        for _ in range(starting_worker_count):
            self.pool.append(worker_cls())
            
        self.checked_out = []

    def get(self):
        # Return a worker if one is pool
        if len(self.pool) > 0:
            worker = self.pool.pop()
            self.checked_out.append(worker)

            return worker

        # Calculate the total number of workers
        total_workers = len(self.checked_out) + len(self.pool)

        # Create a new worker if there are no available workers and the 
        # max worker limit has not yet been reached
        if total_workers < self.max_workers:
            worker = self.worker_cls()
            self.checked_out.append(worker)

            return worker

        # There are no more available workers
        return None

    def join(self, worker):
        if len(self.checked_out) + len(self.pool) + 1 > self.max_workers:
            raise WorkerLimitExceed(f"This WorkerPool has exceed its maximum allowable number of workers ({self.max_workers})")

        self.checked_out.remove(worker)
        self.pool.appendleft(worker)

        



        
        
