from os import stat
import numpy as np
import multiprocessing as mp

from ptlib.core.task import EmptyTask
from ptlib.core.queue import Queue
from ptlib.core.task import Task

from typing import Tuple


class Controller(mp.managers.BaseManager):
    """ The controller. *** COME BACK *** """

    def __init__(self,
                 pipeline: Task,
                 queue_max_size: int = 5,
                 internal_server_address: Tuple[str, int] = ("", 64529)):

        # initialize base manager
        super().__init__(address=internal_server_address)

        # set default input job and fake input queue
        input_job, input_q, = None, Queue()

        # must store queues so they aren't garbage collected
        self._queues = list()

        for task in pipeline.iter_tasks():
            # skip last task
            if task.next is EmptyTask:
                break

            # try to infer output job structure
            input_job, (shape, dtype) = task.infer_structure(input_job)

            # create and store output queue
            output_q = Queue(capacity=queue_max_size, shape=shape, dtype=dtype)
            self._queues.append(output_q)

            # create workers and assign them to task
            task.create_workers(input_q, output_q)

            # set input queue of task.next to output queue of task
            input_q = output_q

            # update task
            task = task.next

        # create workers and assign them to the final task
        task.create_workers(input_q, Queue())

        self.pipeline = pipeline
        self.queue_max_size = queue_max_size

    def run(self):
        # for process start method to spawn
        mp.set_start_method("spawn", force=True)

        # start all worker processes
        for task in self.pipeline.iter_tasks():
            task._start_workers()

        # wait for the workers of each task to sequentially finish
        for task in self.pipeline.iter_tasks():
            task._kill_workers()
            while task._workers_running():
                pass

            print(f"Task Finished: {task}")

        print("controller done")
