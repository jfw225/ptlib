import multiprocessing as mp

from ptlib.core.process import Process
from ptlib.core.queue import Queue


class Controller:
    """ The controller. *** COME BACK *** """

    def __init__(self, Tasks, task_configs):
        self.processes = list()

        input_q = Queue(fake=True)
        while len(Tasks) > 1:
            Task, task_config = Tasks.pop(0), task_configs.pop(0)
            output_q = mp.Queue()
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
