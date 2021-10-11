
from multiprocessing.queues import Queue as mpQueue
from multiprocessing import get_context


class Queue:
    """ Queue. *** COME BACK *** """

    def __init__(self, fake=False, maxsize=0):
        self.fake = fake

        # super().__init__(maxsize=maxsize, ctx=get_context())

        # if fake:
        #     self.get = lambda: None
        #     self.put = lambda x: None

    def get(self):
        return None

    def put(self, x):
        pass
