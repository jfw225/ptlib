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

        # create job mapping
        job_map = task.create_map(self)

        # link queues to memory
        input_job = input_q._link_mem(create_local=True)
        output_q._link_mem()
        meta_q._link_mem()

        # metadata buffer
        metadata_buffer = np.array([time_ns(), time_ns()])

        input_status = BaseQueue.Empty
        while not self.EXIT_FLAG:
            if (input_status := input_q.get()) is BaseQueue.Empty:
                continue
            elif input_status is BaseQueue.Closed:
                break

            metadata_buffer[0] = time_ns()
            output_job = job_map(input_job)
            metadata_buffer[1] = time_ns()
            print("meta q", meta_q.put([metadata_buffer]))

            while output_q.put(output_job) is BaseQueue.Full:
                pass

        print(f"Worker Done -- Task: {task.name} | ID: {self.id}")

    def is_alive(self):
        """
        Indicates if worker is still working on jobs.
        """

        return self._process.is_alive()
