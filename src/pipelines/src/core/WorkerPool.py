from errors.workers import WorkerLimitExceed


class WorkerPool:
    def __init__(self, worker_cls, starting_worker_count, max_workers=1):
        self.max_workers = max_workers

        # Generate the workers
        self.worker_cls = worker_cls
        for _ in range(starting_worker_count):
            self.worker_pool.append(worker_cls())

        self.pool = []
        self.checked_out = []

    def get(self):
        # Return a worker if one is available
        if len(self.avaiable) > 0:
            worker = self.available.pop()
            self.reserved.append(worker)

            return worker

        # Calculate the total number of workers
        total_workers = len(self.checked_out) + len(self.pool)

        # Create a new worker if there are no available workers and the 
        # max worker limit has not yet been reached
        if total_workers < self.max_workers:
            worker = self.worker_cls()
            self.reserved.append(worker)

            return worker

        # There are no more available workers
        return None

    def join(self, worker):
        if len(self.checked_out) + len(self.pool) + 1 > self.max_workers:
            raise WorkerLimitExceed(f"This WorkerPool has exceed its maximum allowable number of workers ({self.max_workers})")

        self.pool.append(worker)

        



        
        
