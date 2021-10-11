
from multiprocessing import Process as mpProcess


class Process(mpProcess):
    """ Process class. *** come back *** """

    def __init__(self, task, task_config, input_q, output_q):
        self.task = task
        self.task_config = task_config
        self.input_q = input_q
        self.output_q = output_q

        super().__init__(daemon=True)

    def run(self):
        """ The main process loop. """

        pass
