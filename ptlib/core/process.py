
from multiprocessing import Process as mpProcess

from ptlib.core.task import Task


class Process(mpProcess):
    """ Process class. *** come back *** """

    def __init__(self, Task, task_config, input_q, output_q):
        self.Task = Task
        self.task_config = task_config
        self.input_q = input_q
        self.output_q = output_q

        super().__init__(target=self.target, daemon=True,
                         args=(Task, task_config, input_q, output_q))

    def target(self, Task, task_config, input_q, output_q):
        """ The main process loop. """
        # make each an argument to the function

        task = self.Task(**self.task_config)
        job_map = task.create_map()

        while not task.EXIT_FLAG:
            input_job = self.input_q.get()
            output_job = job_map(input_job)
            self.output_q.put(output_job)

        self.output_q.put(Task.Exit)
        print("task done")