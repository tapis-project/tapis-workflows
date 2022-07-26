from collections import deque

from errors.workers import WorkerLimitExceed

# TODO Does this need pessimistic locking?
class WorkerPool:
    def __init__(
        self,
        worker_cls,
        starting_worker_count,
        max_workers=1,
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

    def check_out(self):
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

    def check_in(self, worker):
        if worker in self.checked_out:
            self.checked_out.remove(worker)
        
        self.pool.appendleft(worker)
        
        if self.count() > self.max_workers:
            self.pool.remove(worker)
            raise WorkerLimitExceed(f"This WorkerPool has exceed its maximum allowable number of workers ({self.max_workers})")

    def count(self):
        return len(self.checked_out) + len(self.pool)

    def get_all_running(self):
        return self.checked_out
        



        
        
