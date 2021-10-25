from multiprocessing import Process

from ptlib.core.queue import BaseQueue


class Worker(Process):
    """ Worker class. *** come back*** """

    def __init__(self, task, worker_id, input_q, output_q):
        self.EXIT_FLAG = False
        self.id = worker_id

        super().__init__(target=self.work,
                         args=(task, input_q, output_q),
                         daemon=True)

    def work(self, task, input_q, output_q):
        """ 
        The main processing loop for `task`. 
        """

        # create job mapping
        job_map = task.create_map(self)

        # link queues to memory
        input_q._link_mem()
        output_q._link_mem()

        while not self.EXIT_FLAG:
            input_job = input_q.get()
            if input_job is BaseQueue.Empty:
                continue
            elif input_job is BaseQueue.Closed:
                break

            output_job = job_map(input_job)

            while output_q.put(output_job) is BaseQueue.Full:
                pass

        print(f"Worker Done -- Task: {task} | ID: {self.id}")
