import pickle
import numpy as np
from multiprocessing import Queue
from time import time_ns


import ptlib as pt
from ptlib.core.job import Job, JobSpec

# test_batch = pickle.load(open("test_batch.pkl", "rb"))
test_batch = np.zeros((100, 100, 100))

NUM_TESTS = 1000


if __name__ == '__main__':
    print(
        f"Generating {NUM_TESTS} ranom arrays of shape {test_batch.shape}...")
    TEST_ARRAYS = np.array(np.random.rand(
        NUM_TESTS, *test_batch.shape), dtype=test_batch.dtype)

    print("Beginning tests...")

    pt_q = pt.Queue(JobSpec(example=test_batch), capacity=2)
    mp_q = Queue(maxsize=2)

    local_buffer = pt_q._link_mem(create_local=True)
    # testing dynamic code
    # pt_q._generate_dynamic_put()

    t1 = time_ns()
    for batch in TEST_ARRAYS:
        pt_q.put(batch)
        pt_q.get()
    t1 = (time_ns() - t1) / NUM_TESTS
    print(f"PT Average Time: {t1 / 1e9} s")

    t2 = time_ns()
    for batch in TEST_ARRAYS:
        mp_q.put(test_batch)
        mp_q.get()
    t2 = (time_ns() - t2) / NUM_TESTS
    print(f"MP Average Time: {t2 / 1e9} s")

    ratio = t2 / t1
    print(f"PT is {ratio} times faster than MP")
