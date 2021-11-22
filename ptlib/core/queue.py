
from typing_extensions import runtime
import numpy as np
from multiprocessing.shared_memory import SharedMemory
from multiprocessing import Lock

from typing import Tuple
from time import time_ns

from ptlib.core.job import JobSpec, Job


class BaseQueue:
    """ Queue. *** COME BACK *** """

    class Wait:
        """ Flag for lock acquisition wait. """
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

    def put(self):
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
                 capacity: int,
                 job_spec: JobSpec):
        """
        Parameters:
            capacity -- int
                The number of data-sized slots to send data.
            job_spec -- ptlib.core.job.JobSpec
                Specification for the structure of the input job into the queue.
        """

        self.capacity = capacity
        self.job_spec = job_spec

        # define local job buffer
        self._job_buffer = None

        # create shared memory objects
        self._shm_dat = SharedMemory(
            create=True, size=job_spec.get_nbytes(capacity))
        self._shm_sel = SharedMemory(create=True, size=3)
        self._shm_chk = SharedMemory(create=True, size=capacity)

        # initialize selection and check arrays
        np.ndarray(2, dtype=np.int8, buffer=self._shm_sel.buf).fill(0)
        np.ndarray(capacity, dtype=np.int8, buffer=self._shm_chk.buf).fill(0)

        # define arrays
        self._arr_dat = np.ndarray(0)
        self._arr_sel = np.ndarray(0)
        self._arr_chk = np.ndarray(0)

        # create selection lock
        self._lock_sel = Lock()

        # flag to check if arrays have been linked in current context
        self._is_linked = False

    def get(self):
        """
        Attemps to retreive data from shared memory. If the selected index is 
        empty, this returns `BaseQueue.Empty`. If the queue is closed, then 
        `BaseQueue.Closed` is returned. Otherwise, this loads data into 
        `self._arr_dat` and returns True. 
        """

        # acquire selection lock
        self._lock_sel.acquire()

        # get index
        sel_index = self._arr_sel[1]

        # if get index == set index and check[set] is low, wait for check[set] to be high
        if self._arr_chk[sel_index] == 0:  # queue is either empty or closed
            self._lock_sel.release()
            # print(f"sel get: {sel_index} returning False", self._arr_chk[sel_index])

            return BaseQueue.Empty if self._arr_sel[2] == 0 else BaseQueue.Closed

        # increment get index
        self._arr_sel[1] = (sel_index + 1) % self.capacity
        # print(f"sel get: {sel_index}", self._arr_chk[sel_index])

        # get payload (must copy because buffer might change in other process)
        self._job_buffer[:] = self._arr_dat[sel_index]

        # release selection lock
        self._lock_sel.release()

        # set check[get] to low
        self._arr_chk[sel_index] = 0

        return True

    def put(self):
        """
        Attempts to load `self._job_buffer` into shared memory. If the selected 
        index is full, then this returns `BaseQueue.Full`. If the queue is 
        closed, then `BaseQueue.Closed` is returned. Otherwise, this loads data 
        into `self._arr_dat` and returns True. 
        """

        # acquire selection lock
        self._lock_sel.acquire()

        # set index
        sel_index = self._arr_sel[0]

        # if set index == get index and check[get] is high, wait for check[get] to be low
        if self._arr_chk[sel_index] == 1:  # queue is either full or closed
            self._lock_sel.release()
            # print(f"sel put: {sel_index} returning False", self._arr_chk[sel_index])

            return BaseQueue.Full if self._arr_sel[2] == 0 else BaseQueue.Closed

        # increment set index
        self._arr_sel[0] = (sel_index + 1) % self.capacity
        # print(f"sel put: {sel_index}", self._arr_chk[sel_index])

        # print(self._arr_dat, self._job_buffer)
        self._arr_dat[sel_index][:] = self._job_buffer

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

    def _link_mem(self):

        # create local array connected to shared memory buffer
        self._arr_dat = np.ndarray((self.capacity, self.job_spec.get_nbytes()),
                                   dtype=np.int8,
                                   buffer=self._shm_dat.buf)

        # create local job buffer
        local_job = Job(self.job_spec)
        self._job_buffer = local_job._buffer

        # link selection and check arrays to buffers in memory
        self._arr_sel = np.ndarray(
            3, dtype=np.int8, buffer=self._shm_sel.buf)
        self._arr_chk = np.ndarray(
            self.capacity, dtype=np.int8, buffer=self._shm_chk.buf)

        # set linked flag to HIGH
        self._is_linked = True

        return local_job

    # def _generate_dynamic_put(self):
    #     print("generating dynamic put")
    #     f = open("_dptest.py", "w")
    #     f.write("def _put(_job_buffer, buffer, sel_index):\n")
    #     for i in self._iter:
    #         f.write(f"\t_job_buffer[{i}][sel_index]=buffer[{i}]\n")

    #     f.close()

    #     dp = __import__("_dptest", fromlist=["_put"])
    #     self._put = dp._put


def Queue(job_spec: JobSpec = None,
          *,
          capacity: int = 1):
    """
    Returns BaseQueue or FIFOQueue depending on the inputs.
    """

    queue = BaseQueue if job_spec is None else FIFOQueue

    return queue(capacity, job_spec)
