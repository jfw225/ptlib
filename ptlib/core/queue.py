
import numpy as np
from multiprocessing.shared_memory import SharedMemory
from multiprocessing import Lock
from multiprocessing.queues import Queue as mpQueue
from multiprocessing import get_context


class Queue:
    """ Queue. *** COME BACK *** """

    def __init__(self, fake=False, maxsize=0):
        self.fake = fake

        # super().__init__(maxsize=maxsize, ctx=get_context())

        # if fake:
        #     self.get = lambda: None
        #     self.put = lambda x: None

    def get(self):
        return True

    def put(self, x):
        return True

    def _link_mem(self):
        pass


class PTMem:
    """ Object to faciliate memory management across parallel processes. """

    def __init__(self,
                 capacity: int = 1,
                 shape: tuple[int] = None,
                 dtype: np.dtype = None,
                 example: np.ndarray = None):
        """ 
        Parameters: 
            capacity -- the number of data-sized slots to send data

            shape    -- shape of the data
            dtype    -- byte size of the data
            example  -- an example data to infer structure and 
                        space requirements of the data (if provided, shape 
                        and dtype will be ignored)
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
        self.shm_sel = SharedMemory(create=True, size=2)
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

    def _link_mem(self):
        """ Links interal arrays to their buffers in memory. Must be called 
        after new process is spawned. """

        self.arr_dat = np.ndarray(
            self.shape, dtype=self.dtype, buffer=self.shm_dat.buf)
        self.arr_sel = np.ndarray(
            2, dtype=np.int8, buffer=self.shm_sel.buf)
        self.arr_chk = np.ndarray(
            self.capacity, dtype=np.int8, buffer=self.shm_chk.buf)

    def get(self):
        # acquire selection lock
        self.lock_sel.acquire()

        # get index
        i = self.arr_sel[1]

        # if get index == set index and check[set] is low, wait for check[set] to be high
        if self.arr_chk[i] == 0:
            self.lock_sel.release()
            # print(f"sel get: {i} returning False", self.arr_chk[i])
            return False

        # increment get index
        self.arr_sel[1] = (i + 1) % self.capacity
        print(f"sel get: {i}", self.arr_chk[i])

        # get payload
        payload = self.arr_dat[i].copy()

        # release selection lock
        self.lock_sel.release()

        # set check[get] to low
        self.arr_chk[i] = 0

        return payload

    def put(self, buffer):
        # acquire selection lock
        self.lock_sel.acquire()

        # set index
        i = self.arr_sel[0]

        # if set index == get index and check[get] is high, wait for check[get] to be low
        if self.arr_chk[i] == 1:
            self.lock_sel.release()
            # print(f"sel put: {i} returning False", self.arr_chk[i])
            return False

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
