import numpy as np
import multiprocessing as mp

from time import time_ns

from ptlib.core.metadata import MetadataManager
from ptlib.core.task import Task, EmptyTask
from ptlib.core.queue import Queue

from typing import Tuple


class Controller:
    """ The controller. *** COME BACK *** """

    def __init__(self,
                 pipeline: Task,
                 queue_max_size: int = 5):

        # for process start method to spawn correctly
        mp.set_start_method("spawn", force=True)

        # create metadata manager before tasks are set up
        # metadata_manager = MetadataManager()

        # store initialization arguments
        self.pipeline = pipeline
        self.queue_max_size = queue_max_size

        # queue for communicating metadata (replace 30 with something to do with total workers)
        self.meta_q = Queue(
            capacity=30, example=np.array([time_ns(), time_ns()]))

        # set up tasks
        self._set_up_tasks()

    def run(self):
        # start all worker processes
        for task in self.pipeline.iter_tasks():
            task._start_workers()

        # link metadata queue
        meta_q = self.meta_q
        meta_q._link_mem()

        task = self.pipeline
        while task is not EmptyTask:

            # if current task finishes, send kill signal to workers
            if not task._workers_running():
                print(f"Task Finished: {task.name}")
                task = task.next
                task._kill_workers()

        # wait for the workers of each task to sequentially finish
        # for task in self.pipeline.iter_tasks():
        #     task._kill_workers()
        #     while task._workers_running():
        #         pass

        print("controller done")

    def _set_up_tasks(self):
        """
        Sets up each task with the appropriate queue.
        """

        # set default input job and fake input queue
        input_job, input_q, = None, Queue()

        for task in self.pipeline.iter_tasks():
            print(f"Creating Task: {task.name} | ID: {task.id}")

            # skip last task
            if task.next is EmptyTask:
                break

            # try to infer output job structure
            input_job, (shape, dtype) = task.infer_structure(input_job)

            # create and store output queue
            output_q = Queue(capacity=self.queue_max_size,
                             shape=shape, dtype=dtype)

            # set input queue of task (see method documentation for reason)
            task._set_input_queue(input_q)

            # create workers and assign them to task
            task.create_workers(input_q, output_q, self.meta_q)

            # set input queue of task.next to output queue of task
            input_q = output_q

            # update task
            task = task.next

        # like above
        task._set_input_queue(input_q)

        # create workers and assign them to the final task
        task.create_workers(input_q, Queue(), self.meta_q)

    def _add_worker(self, name, task_id, worker_id):
        """
        Called when ptlib.core.worker.Worker is initialized. Registers the
        worker and shared data structures.
        """

        # stores pairs of timestamps of when job starts and finishes
        pairs = self.list()

        # latest job start time
        latest_start = self.Value("i", 0)

        self._worker_map[task_id, worker_id] = (name, pairs, latest_start)
