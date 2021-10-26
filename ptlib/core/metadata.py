from time import time_ns

from ptlib.core.job import JobSpec
from ptlib.core.queue import BaseQueue, Queue


class MetadataManager:
    """ *** COME BACK """

    # job specification for metadata
    _MetaDataSpec = JobSpec(example=[1, 1]) + \
        JobSpec(example=[time_ns(), time_ns()])

    # the queue max size
    meta_q_max_size = 30

    def __init__(self, pipeline):
        # initialize start and finish times
        self._start_time = self._finish_time = None

        # create mappings for worker names and metadata
        self._name_map, self._meta_map = dict(), dict()

        # create initial entries
        for task in pipeline.iter_tasks():
            for worker_id in range(task.num_workers):
                # set name
                self._name_map[task.id,
                               worker_id] = f"{task.name}: {worker_id}"

                # set metadata to empty list
                self._meta_map[task.id, worker_id] = list()

        # queue for retreiving metadata from asnychronous workers
        self.meta_q = Queue(self._MetaDataSpec, capacity=self.meta_q_max_size)

        # link metadata queue and get local buffer
        self._meta_buffer = self.meta_q._link_mem(create_local=True)

    def update(self):
        """
        Update metadata while `self.meta_q` is not empty.
        """

        while self.meta_q.get() is not BaseQueue.Empty:
            index, times = map(tuple, self._meta_buffer)
            self._meta_map[index].append(times)

    def set_time(self):
        """ 
        Used to set main pipeline start and finish times. The first call of 
        tihs function will set the start time, and all subsequent calls will 
        update the finish time. 
        """

        if self._start_time is None:
            self._start_time = time_ns()
        else:
            self._finish_time = time_ns()
