from time import time_ns

import ptlib._backend as ptconfig
from ptlib.core.job import JobSpec
from ptlib.core.queue import BaseQueue, Queue


class MetadataManager:
    """
    Class to abstract metadata initialization and updates. Metadata is 
    transported through a `ptlib.core.queue.FIFOQueue` as if it were a job.

    Attributes:
        metadata_spec -- ptlib.core.job.JobSpec
            The specification for the metadata queue which has two jobs. The 
            first is used to identify the worker and has the structure
            [task id, worker id, S/F indicator], where the S/F indicator is 1 if
            the incoming data is for the start/finish of the worker process, 
            and 0 if the incoming data is for the worker's job. The second job 
            transmitted through the metadata queue is the metadata itself and 
            has the structure
            [start time, finish time], where each time is in nanoseconds.
        meta_q_cap -- int
            The capacity of the metadata queue. 
        _total_jobs -- int
            The number of jobs processed by the pipeline.
        _start -- int
            The start time in nanoseconds of the overall pipeline (the time at 
            which the `run` function of the controller was called). 
        _finish -- int
            The finish time in nanoseconds of the overall pipeline (the time at 
            which the `run` function of the controller terminated. 
        _names -- dict
            Dictionary of worker names where 
            `_names[task id, worker id]=worker name`. 
        _meta -- dict
            Dictionary of metadata where 
            `_meta[task id, worker id][i]=(start time, finish time)`. Note that 
            each start and finish time are in nanoseconds. If `i==0`, then 
            the metadata corresponds to the start or finish of the worker 
            process. Otherwise, the metadata corresponds to the ith job.
        """

    # job specification for metadata (task id, worker id, if data is start/finish time)
    metadata_spec = JobSpec(example=ptconfig._METADATA.JOB_SPEC_EXAMPLES[0]) + \
        JobSpec(example=ptconfig._METADATA.JOB_SPEC_EXAMPLES[1])

    # the queue max size
    meta_q_cap = ptconfig._METADATA.QUEUE_MAX_SIZE

    def __init__(self, pipeline, total_jobs=None):
        # store total number of jobs processed by the pipeline
        self._total_jobs = total_jobs

        # initialize start and finish times
        self._start = self._finish = None

        # create mappings for worker names and metadata
        self._names, self._meta = dict(), dict()

        # create initial entries
        for task in pipeline.iter_tasks():
            for worker_id in range(task.num_workers):
                # set name
                self._names[task.id,
                            worker_id] = f"{task.name}: {worker_id}"

                # set metadata to list with one element (will get overridden in first `update` call)
                self._meta[task.id, worker_id] = [None]

        # queue for retreiving metadata from asnychronous workers
        self.meta_q = Queue(self.metadata_spec,
                            capacity=self.meta_q_cap)

        # link metadata queue and get local buffer
        self._meta_buffer = self.meta_q._link_mem(create_local=True)

    def update(self):
        """
        Update metadata while `self.meta_q` is not empty.
        """

        while self.meta_q.get() is not BaseQueue.Empty:
            # get the index and new metadata
            (*index, sf_ind), new_meta = map(tuple, self._meta_buffer)

            # if the S/F indicator is HIGH, set the first index
            if sf_ind == 1:
                self._meta[tuple(index)][0] = new_meta

            # otherwise add job metadata to list
            else:
                self._meta[tuple(index)].append(new_meta)

    def set_time(self):
        """ 
        Used to set main pipeline start and finish times. The first call of 
        tihs function will set the start time, and all subsequent calls will 
        update the finish time. 
        """

        if self._start is None:
            self._start = time_ns()
        else:
            self._finish = time_ns()
