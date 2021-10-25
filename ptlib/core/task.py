import numpy as np

from ptlib._typing import Job
from ptlib.errors import WorkerCreationError, WorkerStartError
from ptlib.core.queue import Queue
from ptlib.core.worker import Worker


class EmptyTask:
    pass


class Task:
    """ 
    Template class for making new Task objects. 

    Parameters:
        config -- ptlib.task.config
            Task configuaration object used to set up task at runtime.

    Attributes:
        config -- ptlib.task.config
            Task configuration object passed at runtime.
        EXIT_FLAG -- bool
            Used to determine loop termination in process.
    """

    class Exit:
        pass

    # ---------------------------------------------------------------------- #
    # Constructors

    def __init__(self, num_workers):
        self.num_workers = num_workers
        self.workers = list()
        self.next = EmptyTask
        self.input_q = Queue()

    def create_map(self, worker: Worker):
        """
        Returns a function that maps input job to output job for a specific 
        worker. The returned function `map_job` should evaluate an expression 
        to determine the value of `worker.EXIT_FLAG`. `create_map` should be 
        overloaded.
        """

        def map_job(job):
            if job is Task.Exit:
                worker.EXIT_FLAG = True

            return job

        return map_job

    def create_workers(self, input_q, output_q):
        """
        Returns a list of pt.Worker objects and stores input queue. Overloading 
        this function allows the developer to modify the controller's 
        instructions for worker creation. 
        """

        if len(self.workers) > 0:
            raise WorkerCreationError(
                f"Workers already exist for task: {self}")

        for worker_id in range(self.num_workers):
            self.workers.append(Worker(self, worker_id, input_q, output_q))

        self.input_q = input_q

    def infer_structure(self, input_job):
        """ 
        Tries to infer the structure (shape, dtype) of task's output job an 
        example input job. This is done by creating (and later deleting) a 
        temporary worker to analyze the output of `map_job(input_job)`.
        """

        worker = Worker(self, 0, Queue(), Queue())
        job_map = self.create_map(worker)
        output_job = np.array(job_map(input_job))

        return output_job, (output_job.shape, output_job.dtype)

    def __rshift__(self, other):
        """ 
        Allows tasks to be connected into a pipeline using the `>>` operator. 
        """

        if isinstance(other, Task):
            task = self
            while task.next is not EmptyTask:
                task = task.next

            task.next = other

        return self

    def cleanup(self):
        """ 
        Routine for task cleanup after termination. This function should be 
        overloaded if needed. 
        """

        pass

    def iter_tasks(self):
        task = self
        while task is not EmptyTask:
            yield task
            task = task.next

    def _start_workers(self):
        """ 
        Starts each of the worker processes. This should not be overloaded. 
        """

        if len(self.workers) == 0:
            raise WorkerStartError(
                f"Workers have not been created for task: {self}")

        for worker in self.workers:
            worker.start()

    def _workers_running(self):
        """
        Returns True if workers are still running, False if otherwise. 
        """

        return any([worker.is_alive() for worker in self.workers])

    def _kill_workers(self):
        """
        Signals workers to exit by closing their input queue. 
        """

        self.input_q.close()
