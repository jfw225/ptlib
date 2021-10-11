import numpy as np
import multiprocessing as mp

from ptlib.core.process import Process
from ptlib.core.queue import Queue, PTMem


class Controller:
    """ The controller. *** COME BACK *** """

    def __init__(self, Tasks, task_configs, queue_max_size=5):
        self.processes = list()

        input_q = Queue(fake=True)
        input_job = None
        while len(Tasks) > 1:
            Task, task_config = Tasks.pop(0), task_configs.pop(0)

            # try to infer output job structure
            input_job, (shape, dtype) = self.infer_structure(
                Task, task_config, input_job)

            # output_q = mp.Queue()
            output_q = PTMem(capacity=queue_max_size, shape=shape, dtype=dtype)
            self.processes.append(
                Process(Task, task_config, input_q, output_q))
            input_q = output_q

        Task, task_config = Tasks.pop(), task_configs.pop()
        self.processes.append(
            Process(Task, task_config, input_q, Queue(fake=True)))

    def run(self):
        for p in self.processes:
            p.start()

        while any([p.is_alive() for p in self.processes]):
            pass

        print("done")

    @staticmethod
    def infer_structure(Task, task_config, input_job):
        task = Task(**task_config)
        job_map = task.create_map()
        output_job = np.array(job_map(input_job))
        print(output_job.shape, output_job.dtype)

        return output_job, (output_job.shape, output_job.dtype)
