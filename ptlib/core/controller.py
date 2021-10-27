import numpy as np
import multiprocessing as mp

from time import time_ns
from ptlib.core.job import JobSpec

from ptlib.core.metadata import MetadataManager
from ptlib.core.task import Task, EmptyTask
from ptlib.core.queue import BaseQueue, Queue

from typing import Tuple

from ptlib.utils.diagram import Diagram


class Controller:
    """ The controller. *** COME BACK *** """

    def __init__(self,
                 pipeline: Task,
                 queue_max_size: int = 5):

        # for process start method to spawn correctly
        mp.set_start_method("spawn", force=True)

        # create metadata manager before tasks are set up
        self.meta_manager = MetadataManager(pipeline)

        # store initialization arguments
        self.pipeline = pipeline
        self.queue_max_size = queue_max_size

        # set up tasks
        self._set_up_tasks()

    def run(self):
        """ 
        The main run loop for the pipeline. 
        """

        # set start time
        self.meta_manager.set_time()

        # start all worker processes
        for task in self.pipeline.iter_tasks():
            task._start_workers()

        task = self.pipeline
        while task is not EmptyTask:
            # update metadata
            self.meta_manager.update()

            # if current task finishes, send kill signal to workers
            if not task._workers_running():
                print(f"Task Finished: {task.name}")
                task = task.next
                task._kill_workers()

        # finish retreiving metadata (in case loop exits before getting all metadata)
        self.meta_manager.update()

        # set finish time
        self.meta_manager.set_time()

        print(self.meta_manager._meta)
        print("controller done")

    def graph(self, save_path=""):
        """
        Creates and shows parallel timing diagram. If `save_path` is empty, then 
        the graphs are shown. Otherwise, the graphs are written to 
        `save_path` as a .pkl file. 
        """

        diag = Diagram(meta_manager=self.meta_manager)
        diag.graph_all(save_path)

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
            input_job, job_specs = task.infer_structure(input_job)

            # create and store output queue
            output_q = Queue(job_specs, capacity=self.queue_max_size)

            # set input queue of task (see method documentation for reason)
            task._set_input_queue(input_q)

            # create workers and assign them to task
            task.create_workers(input_q, output_q,
                                self.meta_manager.meta_q)

            # set input queue of task.next to output queue of task
            input_q = output_q

            # update task
            task = task.next

        # like above
        task._set_input_queue(input_q)

        # create workers and assign them to the final task
        task.create_workers(input_q, Queue(), self.meta_manager.meta_q)

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
