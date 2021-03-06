from multiprocessing import Process
from time import time_ns

from ptlib.core.queue import BaseQueue


class Worker(Process):
    """ Worker class. *** come back*** """

    def __init__(self, Task, num_workers, task_id, worker_id, input_q, output_q, meta_q):
        self.EXIT_FLAG = False
        self.num_workers = num_workers
        self.task_id = task_id
        self.id = worker_id

        # create worker process
        super().__init__(target=self.work,
                         args=(Task, input_q,
                               output_q, meta_q),
                         daemon=True)

    def work(self, Task, input_q, output_q, meta_q):
        """
        The main processing loop for `task`.
        """

        # create task object and set correct task id
        task = Task(num_workers=self.num_workers, task_id=self.task_id)

        # link queues to memory
        input_job = input_q._link_mem()
        output_job = output_q._link_mem()
        meta_buffer = meta_q._link_mem()

        # set up local metadata buffers
        id_buffer = meta_buffer["id"]
        data_buffer = meta_buffer["data"]

        # set the first job in buffer to (task id, worker id, and S/F indicator to HIGH)
        id_buffer[:] = [task.id, self.id, 1][:]

        # give main thread worker start time
        start_time = time_ns()
        data_buffer[:] = [start_time, start_time][:]
        # (if metadata seems off, add while loop)
        assert meta_q.put() is not BaseQueue.Full, "meta q should always put (prejob)"

        # set S/F indicator to LOW
        id_buffer[-1] = 0

        # create job mapping
        job_map = task.create_map(self, input_job, output_job)

        input_status = BaseQueue.Empty

        while not self.EXIT_FLAG:
            # t = time_ns()
            if (input_status := input_q.get()) is BaseQueue.Empty:
                continue
            elif input_status is BaseQueue.Closed:
                break
            # print(f"Task: {task.id} | Get Time: {time_ns() - t}")

            # record start time
            data_buffer[0] = time_ns()

            # map input job to compute output job
            job_map()

            # print(output_job_buf)
            # if output_job[0] is not None:
            #     for i in range(len(output_job)):
            #         print(output_job_buf[i].shape, output_job[i].shape)
            #         output_job_buf[i][:] = output_job[i]

            # record finish time
            data_buffer[1] = time_ns()

            # put metadata into queue (if metadata seems off, add while loop)
            assert meta_q.put() is not BaseQueue.Full, "meta q should always put"

            t = time_ns()
            while output_q.put() is BaseQueue.Full:
                pass
            # print(f"Task: {task.id} | Put Time: {(time_ns() - t)/1e9}")

        # run cleanup routine
        task.cleanup()

        # record finish time
        finish_time = time_ns()

        # set S/F indicator to HIGH
        id_buffer[-1] = 1

        # give main thread worker finish time
        data_buffer[:] = [start_time, finish_time][:]
        meta_q.put()  # (if metadata seems off, add while loop)

        print(f"Worker Done -- Task: {task.name} | ID: {self.id}")
