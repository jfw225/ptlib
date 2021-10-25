import multiprocessing as mp
from multiprocessing.managers import BaseManager, SyncManager

from ptlib.core._backend import SERVER_ADDRESS


def test():
    print("test")


class MetadataManager(SyncManager):
    """ *** COME BACK """

    def __init__(self):
        """
        Must pass the base manager to make `add_worker` available in the
        asynchronous scope.
        """

        # initialize multiprocessing manager
        super().__init__(address=SERVER_ADDRESS)

        # register `add_worker` with the base manager
        self.register(self._add_worker.__name__, callable=self._add_worker)
        self._worker_map = self.dict()

        # start backend server
        self.start()

        # create worker map
        print(self._worker_map)

    def _add_worker(self, name, task_id, worker_id):
        """
        Called when ptlib.core.worker.Worker is initialized. Registers the
        worker and shared data structures.
        """

        print("hi")

        # stores pairs of timestamps of when job starts and finishes
        # pairs = self.list()

        # # latest job start time
        # latest_start = self.Value("i", 0)

        # self._worker_map[task_id, worker_id] = (name, pairs, latest_start)

        return self._worker_map, self._worker_map
