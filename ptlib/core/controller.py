from os import stat
import numpy as np
import multiprocessing as mp

from ptlib.core.task import EmptyTask
from ptlib.core.queue import Queue, PTMem
from ptlib.core.task import Task


class Controller:
    """ The controller. *** COME BACK *** """

    def __init__(self, pipeline, queue_max_size=5):
        # set default input job and fake input queue
        input_job, input_q, = None, Queue(fake=True)

        # must store queues so they aren't garbage collected
        self._queues = list()

        for task in pipeline.iter_tasks():
            # skip last task
            if task.next is EmptyTask:
                break

            # try to infer output job structure
            input_job, (shape, dtype) = task.infer_structure(input_job)

            # create and store output queue
            output_q = PTMem(capacity=queue_max_size, shape=shape, dtype=dtype)
            self._queues.append(output_q)

            # create workers and assign them to task
            task.create_workers(input_q, output_q)

            # set input queue of task.next to output queue of task
            input_q = output_q

            # update task
            task = task.next

        # create workers and assign them to the final task
        task.create_workers(input_q, Queue(fake=True))

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
            while task._workers_running():
                pass

            print(f"Task Finished: {task}")

        print("controller done")
