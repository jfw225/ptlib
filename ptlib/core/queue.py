
from typing_extensions import runtime
import numpy as np
from multiprocessing.shared_memory import SharedMemory
from multiprocessing import Lock

from typing import Tuple
from time import time_ns

from ptlib.core.job import JobSpec, Job


class BaseQueue:
    """ Queue. *** COME BACK *** """

    class Empty:
        """ Flag for emtpy queue. """

    class Full:
        """ Flag for full queue. """

    class Closed:
        """ Flag for closed queue. """

    def __init__(self, *args, **kwargs):
        self.job = None

    def get(self):
        return []

    def put(self, x):
        return True

    def close(self):
        pass

    def _link_mem(self, create_local=False):
        pass


class FIFOQueue(BaseQueue):
    """ Object to faciliate memory management across parallel processes. 

    Attributes: (** update with jobs and replace arr with buffer or buf)
        _job_buffer -- ptlib.core.job.Job or (capacity x shape)-darray 
            Array of arrays linked to the shared memory buffer for asynchronous 
            data transfer.
        _local_job_buffer -- ptlib.core.job.Job or shape-darray
            Local copy of a single job used to load a temporary copy of an 
            _job_buffer[i]. This is only created if `_link_mem` is called with 
            kwarg `create_local=True`. Very important that this is created if 
            queue is acting as an input or else data in `_job_buffer` might get 
            overwritten by an upstream task before it is used.
        _arr_sel -- (3 x 1)-darray
            Buffer with following elements:
                =+= `arr_sel[0]=i` indicates that `put()` will store data in 
                    `arr_dat[i]` 
                =+= `arr_sel[1]=j` indicates that `get()` will retreive data 
                    from `arr_dat[j]`.
                =+= `arr_sel[0]=k` where `k==0` indicates queue is open and 
                    `k==1` indicates queue is closed.
        _arr_chk -- (capacity x 1)-darray
            Buffer where each `arr_chk[i]` is 0 if `arr_dat[i]` is full or 1 if 
            `arr_dat[i]` is empty.
        """

    def __init__(self,
                 job_specs: JobSpec,
                 capacity: int = 1):
        """
        Parameters:
            capacity -- int
                The number of data-sized slots to send data.
            job_spec -- ptlib.core.job.JobSpec
                Specification for the structure of the input job into the queue.
        """

        self.capacity = capacity

        # make copy of job specifications
        self._job_specs = [job_spec for job_spec in job_specs]

        # iterate over job specifications and allocate memory
        self._job_shms = list()
        self._job_buffer = self._local_job_buffer = None
        for job_spec in job_specs:
            # cast to np.ulonglong or else `data_nbytes` will be incorrect
            job_spec.shape = np.array(
                (capacity, *job_spec.shape), dtype=np.ulonglong)

            data_nbytes = int(np.nbytes[job_spec.dtype]
                              * np.product(job_spec.shape))

            self._job_shms.append(SharedMemory(create=True, size=data_nbytes))

        # create shared memory objects
        self._shm_sel = SharedMemory(create=True, size=3)
        self._shm_chk = SharedMemory(create=True, size=capacity)

        # initialize selection and check arrays
        np.ndarray(2, dtype=np.int8, buffer=self._shm_sel.buf).fill(0)
        np.ndarray(capacity, dtype=np.int8, buffer=self._shm_chk.buf).fill(0)

        # declare arrays
        self._arr_sel = np.ndarray(0)
        self._arr_chk = np.ndarray(0)

        # create and store arange to avoid repeated creation
        self._iter = np.arange(len(job_specs))

        # create selection lock
        self._lock_sel = Lock()

        # flag to check if arrays have been linked in current context
        self._is_linked = False

    def get(self):
        """
        Attemps to retreive data from shared memory. If the selected index is 
        empty, this returns `BaseQueue.empty`. If the queue is closed, then 
        `BaseQueue.Closed` is returned. Otherwise, this loads data into 
        `self._local_job_buffer` and returns True. 
        """

        # acquire selection lock
        self._lock_sel.acquire()

        # get index
        sel_index = self._arr_sel[1]

        # if get index == set index and check[set] is low, wait for check[set] to be high
        if self._arr_chk[sel_index] == 0:
            self._lock_sel.release()
            # print(f"sel get: {sel_index} returning False", self._arr_chk[sel_index])
            # if `arr_chk[sel_index] == 0 && arr_sel[2] == 1` then queue must be closed
            return BaseQueue.Empty if self._arr_sel[2] == 0 else BaseQueue.Closed

        # increment get index
        self._arr_sel[1] = (sel_index + 1) % self.capacity
        # print(f"sel get: {sel_index}", self._arr_chk[sel_index])

        # get payload (must copy because buffer might change in other process)
        for i in self._iter:
            self._local_job_buffer[i][:] = self._job_buffer[i][sel_index]

        # self.input_buffer[:] = self.arr_dat[sel_index][:]

        # release selection lock
        self._lock_sel.release()

        # set check[get] to low
        self._arr_chk[sel_index] = 0

        return True

    def put(self, buffer):
        """
        Attempts to load `buffer` into shared memory. If the selected index is 
        full, then this returns `BaseQueue.Full`. If the queue is closed, then 
        `BaseQueue.Closed` is returned. Otherwise, this loads data into 
        `self._job_buffer` and returns True. 
        """

        # acquire selection lock
        t = time_ns()
        self._lock_sel.acquire()
        print((time_ns() - t)/1e9)

        # set index
        sel_index = self._arr_sel[0]

        # if set index == get index and check[get] is high, wait for check[get] to be low
        if self._arr_chk[sel_index] == 1:
            self._lock_sel.release()
            # print(f"sel put: {sel_index} returning False", self._arr_chk[sel_index])
            # if `arr_chk[sel_index] == 1 && arr_sel[2] == 1` then queue must be closed
            assert self._arr_sel[2] == 0, "should never try to put to a closed array"
            return BaseQueue.Full if self._arr_sel[2] == 0 else BaseQueue.Closed

        # increment set index
        self._arr_sel[0] = (sel_index + 1) % self.capacity
        # print(f"sel put: {sel_index}", self._arr_chk[sel_index])

        # set payload
        # t = time_ns()  # REMOVE
        for i in self._iter:
            self._job_buffer[i][sel_index][:] = buffer[i]
        # print(f"Task: {0} | Buffer Load: {(time_ns() - t)/1e9}")

        # release selection lock
        self._lock_sel.release()

        # set check[set] to high
        self._arr_chk[sel_index] = 1

        return True

    def close(self):
        """
        Closes queue by setting `self._arr_sel[2]` to HIGH.
        """

        # link selection array if it isn't already
        if not self._is_linked:
            self._arr_sel = np.ndarray(
                3, dtype=np.int8, buffer=self._shm_sel.buf)

        # set `self._arr_sel[2]` to HIGH
        self._arr_sel[2] = 1

    def _link_mem(self, create_local=False):
        """ 
        Links interal arrays to their buffers in memory. Must be called
        after new process is spawned. If `create_local` is True, then this 
        createsand returns a local buffer that is filled during `get` calls. 
        Regardless, this process sets `self._is_linked` to HIGH. 
        """

        # allocate new job buffers and link them to their buffers in memory
        self._job_buffer = Job(self._job_specs, buffers=self._job_shms)

        # drop `self.capacity` from each job spec and create job arrays
        if create_local:
            self._local_job_buffer = Job(
                [JobSpec(job_spec.shape[1:], job_spec.dtype)
                 for job_spec in self._job_specs])

        # link selection and check arrays to buffers in memory
        self._arr_sel = np.ndarray(
            3, dtype=np.int8, buffer=self._shm_sel.buf)
        self._arr_chk = np.ndarray(
            self.capacity, dtype=np.int8, buffer=self._shm_chk.buf)

        # set linked flag to HIGH
        self._is_linked = True

        return self._local_job_buffer

    # def _generate_dynamic_put(self):
    #     print("generating dynamic put")
    #     f = open("_dptest.py", "w")
    #     f.write("def _put(_job_buffer, buffer, sel_index):\n")
    #     for i in self._iter:
    #         f.write(f"\t_job_buffer[{i}][sel_index]=buffer[{i}]\n")

    #     f.close()

    #     dp = __import__("_dptest", fromlist=["_put"])
    #     self._put = dp._put


def Queue(job_specs: JobSpec = None,
          *,
          capacity: int = 1):
    """
    Returns BaseQueue or FIFOQueue depending on the inputs.
    """

    queue = BaseQueue if job_specs is None else FIFOQueue

    return queue(job_specs, capacity=capacity)
