
from multiprocessing.queues import Queue as mpQueue
from multiprocessing import get_context


class Queue(mpQueue):
    """ Queue. *** COME BACK *** """

    def __init__(self, fake=False, maxsize=0):
        super().__init__(maxsize=maxsize, ctx=get_context())

        if fake:
            self.get = lambda: None
            self.put = lambda x: None
