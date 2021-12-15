from typing import Iterable
import numpy as np

from ptlib.core.job import Job, Job
from ptlib.errors import WorkerCreationError, WorkerStartError
from ptlib.core.queue import Queue
from ptlib.core.worker import Worker


class EmptyTask:
    def _kill_workers():
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

    def __init__(self, num_workers: int = 1, task_id: int = 0):
        """
        When subclassing `Task`, do not implement a different init, or if you 
        do, don't change the arguments.
        """

        self.num_workers = num_workers
        self.id = task_id

        self.workers = list()
        self.next = EmptyTask
        self.input_q = Queue()

    @property
    def ttype(self):
        """
        The task type. 
        """

        return self.__class__

    @property
    def name(self):
        """
        Formats the name of the task instance by looking at the class
        definition.
        """

        return self.ttype.__name__

    # ---------------------------------------------------------------------- #
    # Methods that can be Overloaded by Developer

    def create_map(self, worker: Worker, input_job, output_job):
        """
        Returns a function that maps input job to output job for a specific
        worker.

        The returned function `map_job` should evaluate an expression
        to determine the value of `worker.EXIT_FLAG`. It should also do
        something with each sub job in `input_job: ptlib.core.job.Job` update
        each subjob in `output_job: ptlic.core.job.Job`.

        The default `create_map` should be overloaded.
        """

        def map_job():
            # example exit
            if input_job is Task.Exit:
                worker.EXIT_FLAG = True

            # example modification
            output_job = input_job.copy()
            for i in range(len((input_job))):
                output_job[i][:] = input_job[i][:]

            return output_job

        return map_job

    def get_example_job(self):
        """
        Returns an object resembling the output job of this task. If this is 
        not overloaded by the developer, the controller will try to infer the 
        structure of the output job. 
        """

        return None

    def create_workers(self, input_q, output_q, meta_q):
        """
        Returns a list of pt.Worker objects and stores input queue. Overloading
        this function allows the developer to modify the controller's
        instructions for worker creation.
        """

        if len(self.workers) > 0:
            raise WorkerCreationError(
                f"Workers already exist for task: {self}")

        # create workers
        from copy import copy
        for worker_id in range(self.num_workers):
            self.workers.append(
                Worker(self.ttype, self.num_workers, self.id, worker_id, input_q, output_q, meta_q))

    def get_total_jobs(self):
        """
        Returns the number of jobs processed by the pipeline. This is used for 
        runtime analytics. If needed, this should be overloaded in the first 
        task of the pipeline. 
        """

        return None

    def cleanup(self):
        """
        Routine for task cleanup after termination. This function should be
        overloaded if needed.
        """

        pass

    # ---------------------------------------------------------------------- #
    # Private and Protected Methods

    def _infer_structure(self, input_job):
        """
        Tries to infer the structure (shape, dtype) of task's output job an
        example input job. This is done by creating (and later deleting) a
        temporary worker to analyze the output of `map_job(input_job)`.
        """

        input_job = self.get_example_job() or input_job

        worker = Worker(self.ttype, 0, 0, 0, Queue(), Queue(), Queue())
        output_job = Job()
        self.create_map(worker, input_job, output_job)()
        job_spec, ouput_job = output_job.infer()

        return job_spec, output_job

    def iter_tasks(self):
        """
        Generator that iterates over linked list structure of tasks using the
        `task.next` attribute.
        """

        task = self
        while task is not EmptyTask:
            yield task
            task = task.next

    def _set_input_queue(self, input_q):
        """
        Sets `self.input_q=input_q`. This is important because it guarantees
        that each queue is not accidently garbage collected before it's used.
        Also needed in 'self._kill_workers`.
        """

        self.input_q = input_q

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

    def __rshift__(self, other):
        """
        Allows tasks to be connected into a pipeline using the `>>` operator.
        This operation finds the last task in linked list of tasks by iterating
        over the `task.next` attribute. Assigns `other.id` to the last
        task ID + 1.
        """

        if not isinstance(other, Task):
            return self

        task = self
        while task.next is not EmptyTask:
            task = task.next

        other.id = task.id + 1
        task.next = other

        return self

    # ---------------------------------------------------------------------- #
