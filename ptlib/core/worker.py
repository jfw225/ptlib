import numpy as np

from multiprocessing.managers import BaseManager
from multiprocessing import Process
from time import time_ns

from ptlib.core._backend import SERVER_ADDRESS
from ptlib.core.metadata import MetadataManager
from ptlib.core.queue import BaseQueue


class Worker(BaseManager):
    """ Worker class. *** come back*** """

    def __init__(self, task, worker_id, input_q, output_q, meta_q):
        self.EXIT_FLAG = False
        self.id = worker_id

        # create worker process
        self._process = Process(target=self.work,
                                args=(task, input_q, output_q, meta_q),
                                daemon=True)

        # initialize multiprocessing base manager
        super().__init__(address=SERVER_ADDRESS)

        # connect to metadata server and register add worker function
        # self.register(MetadataManager._add_worker.__name__)
        # self.connect()
        # # self.start()

        # # get metadata shared memory objects
        # pairs, latest_on = getattr(self, MetadataManager._add_worker.__name__)(
        #     task.name, task.id, self.id)

        # print(pairs, latest_on)

    def work(self, task, input_q, output_q, meta_q):
        """
        The main processing loop for `task`.
        """

        # link queues to memory
        input_job = input_q._link_mem(create_local=True)
        output_q._link_mem()
        meta_buffer = meta_q._link_mem(create_local=True)

        # set the first job in buffer to (task id, worker id, and S/F indicator to HIGH)
        meta_buffer[0][:] = [task.id, self.id, 1][:]

        # metadata time buffer
        time_array = meta_buffer[1]

        # give main thread worker start time
        start_time = time_ns()
        time_array[:] = [start_time, start_time][:]
        # (if metadata seems off, add while loop)
        assert meta_q.put(
            meta_buffer) is not BaseQueue.Full, "meta q should always put (prejob)"

        # set S/F indicator to LOW
        meta_buffer[0][-1] = 0

        # create job mapping
        job_map = task.create_map(self)

        input_status = BaseQueue.Empty
        while not self.EXIT_FLAG:
            t = time_ns()
            if (input_status := input_q.get()) is BaseQueue.Empty:
                continue
            elif input_status is BaseQueue.Closed:
                break
            print(f"Task: {task.id} | Get Time: {time_ns() - t}")

            # record start time
            time_array[0] = time_ns()

            # map compute output job
            output_job = job_map(input_job)

            # record finish time
            time_array[1] = time_ns()

            # put metadata into queue (if metadata seems off, add while loop)
            assert meta_q.put(
                meta_buffer) is not BaseQueue.Full, "meta q should always put"

            t = time_ns()
            while output_q.put(output_job) is BaseQueue.Full:
                pass
            print(f"Task: {task.id} | Put Time: {(time_ns() - t)/1e9}")

        # record finish time
        finish_time = time_ns()

        # set S/F indicator to HIGH
        meta_buffer[0][-1] = 1

        # give main thread worker finish time
        time_array[:] = [start_time, finish_time][:]
        meta_q.put(meta_buffer)  # (if metadata seems off, add while loop)

        print(f"Worker Done -- Task: {task.name} | ID: {self.id}")

    def is_alive(self):
        """
        Indicates if worker is still working on jobs.
        """

        return self._process.is_alive()
