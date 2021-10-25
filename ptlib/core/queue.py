
import numpy as np
from multiprocessing.shared_memory import SharedMemory
from multiprocessing import Lock

from typing import Tuple


class BaseQueue:
    """ Queue. *** COME BACK *** """

    class Empty:
        """ Flag for emtpy queue. """

    class Full:
        """ Flag for full queue. """

    class Closed:
        """ Flag for closed queue. """

    def __init__(self, *args):
        pass

        # super().__init__(maxsize=maxsize, ctx=get_context())

        # if fake:
        #     self.get = lambda: None
        #     self.put = lambda x: None

    def get(self):
        return True

    def put(self, x):
        return True

    def close(self):
        pass

    def _link_mem(self):
        pass


class FIFOQueue(BaseQueue):
    """ Object to faciliate memory management across parallel processes. 

    Attributes:
        arr_dat -- (capacity x shape)-darray 
            Buffer for asynchronous data transfer.
        arr_sel -- (3 x 1)-darray
            Buffer with following elements:
                =+= `arr_sel[0]=i` indicates that `put()` will store data in 
                    `arr_dat[i]` 
                =+= `arr_sel[1]=j` indicates that `get()` will retreive data 
                    from `arr_dat[j]`.
                =+= `arr_sel[0]=k` where `k==0` indicates queue is open and 
                    `k==1` indicates queue is closed.
        arr_chk -- (capacity x 1)-darray
            Buffer where each `arr_chk[i]` is 0 if `arr_dat[i]` is full or 1 if 
            `arr_dat[i]` is empty.
        """

    def __init__(self,
                 capacity: int = 1,
                 shape: Tuple[int] = None,
                 dtype: np.dtype = None,
                 example: np.ndarray = None):
        """
        Parameters:
            capacity -- int
                The number of data-sized slots to send data.
            shape -- Tuple[int]
                The shape of the data.
            dtype -- np.dtype
                The type of the data.
            example -- ndarray
                An example data to infer structure and space requirements of 
                the data (if provided, shape and dtype will be ignored)
        """

        self.capacity = capacity
        shape = example.shape if isinstance(example, np.ndarray) else shape
        self.shape = np.array((capacity, *shape), dtype=np.ulonglong)
        self.dtype = example.dtype if isinstance(
            example, np.ndarray) else dtype

        # calculate number of bytes for data
        data_nbytes = int(np.nbytes[self.dtype] * np.product(self.shape))

        # create shared memory objects
        self.shm_dat = SharedMemory(create=True, size=data_nbytes)
        self.shm_sel = SharedMemory(create=True, size=3)
        self.shm_chk = SharedMemory(create=True, size=capacity)

        # initialize selection and check arrays
        np.ndarray(2, dtype=np.int8, buffer=self.shm_sel.buf).fill(0)
        np.ndarray(capacity, dtype=np.int8, buffer=self.shm_chk.buf).fill(0)

        # declare arrays
        self.arr_dat = np.ndarray(0)
        self.arr_sel = np.ndarray(0)
        self.arr_chk = np.ndarray(0)

        # create selection lock
        self.lock_sel = Lock()

        # flag to check if arrays have been linked in current context
        self._is_linked = False

    def get(self):
        """
        If `self.arr_dat[current index]` is empty, returns `BaseQueue.empty`. 
        Otherwise, loads the data into `self.buffer` and returns it. 
        """

        # acquire selection lock
        self.lock_sel.acquire()

        # get index
        i = self.arr_sel[1]

        # if get index == set index and check[set] is low, wait for check[set] to be high
        if self.arr_chk[i] == 0:
            self.lock_sel.release()
            # print(f"sel get: {i} returning False", self.arr_chk[i])
            # if `arr_chk[i] == 0 && arr_sel[2] == 1` then queue must be closed
            return BaseQueue.Empty if self.arr_sel[2] == 0 else BaseQueue.Closed

        # increment get index
        self.arr_sel[1] = (i + 1) % self.capacity
        print(f"sel get: {i}", self.arr_chk[i])

        # get payload (must copy because buffer might change in other process)
        self.input_buffer[:] = self.arr_dat[i][:]

        # release selection lock
        self.lock_sel.release()

        # set check[get] to low
        self.arr_chk[i] = 0

        return self.input_buffer

    def put(self, buffer):
        """
        If `self.arr_dat[current index]` is full, returns `BaseQueue.Full`.
        Otherwise, loads the data into `buffer`. 
        """
        # acquire selection lock
        self.lock_sel.acquire()

        # set index
        i = self.arr_sel[0]

        # if set index == get index and check[get] is high, wait for check[get] to be low
        if self.arr_chk[i] == 1:
            self.lock_sel.release()
            # print(f"sel put: {i} returning False", self.arr_chk[i])
            # if `arr_chk[i] == 1 && arr_sel[2] == 1` then queue must be closed
            assert self.arr_sel[2] == 0, "should never try to put to a closed array"
            return BaseQueue.Full if self.arr_sel[2] == 0 else BaseQueue.Closed

        # increment set index
        self.arr_sel[0] = (i + 1) % self.capacity
        print(f"sel put: {i}", self.arr_chk[i])

        # set payload
        self.arr_dat[i][:] = buffer[:]

        # release selection lock
        self.lock_sel.release()

        # set check[set] to high
        self.arr_chk[i] = 1

        return True

    def close(self):
        """
        Closes queue by setting `self.arr_sel[2]` to HIGH.
        """

        # link selection array if it isn't already
        if not self._is_linked:
            self.arr_sel = np.ndarray(
                3, dtype=np.int8, buffer=self.shm_sel.buf)

        # set `self.arr_sel[2]` to HIGH
        self.arr_sel[2] = 1

    def _link_mem(self):
        """ 
        Links interal arrays to their buffers in memory. Must be called
        after new process is spawned. Also creates local buffer to fill during
        `get` calls and sets `self._is_linked` to HIGH. 
        """

        # link arrays to buffers in memory
        self.arr_dat = np.ndarray(
            self.shape, dtype=self.dtype, buffer=self.shm_dat.buf)
        self.arr_sel = np.ndarray(
            3, dtype=np.int8, buffer=self.shm_sel.buf)
        self.arr_chk = np.ndarray(
            self.capacity, dtype=np.int8, buffer=self.shm_chk.buf)
        self.input_buffer = np.zeros(self.shape[1:], dtype=self.dtype)

        # set linked flag to HIGH
        self._is_linked = True


def Queue(*,
          capacity: int = 1,
          shape: Tuple[int] = None,
          dtype: np.dtype = None,
          example: np.ndarray = None):
    """
    Returns BaseQueue or FIFOQueue depending on the inputs.
    """

    fake = (shape is None or dtype is None) and example is None
    queue = BaseQueue if fake else FIFOQueue

    return queue(capacity, shape, dtype, example)
