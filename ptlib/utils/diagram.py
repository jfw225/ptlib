
from typing import Iterable

from ptlib.core.metadata import MetadataManager


class DiagramSpec:
    """ *** come back """

    def __init__(self,
                 start_time: int,
                 finish_time: int,
                 process_names: dict[str],
                 metadata: dict[int, int]):
        """
        Parameters:
            start_time -- int
                The start time of the main process in nanoseconds.
            finish_time: int
                The finish time of the main process in nanoseconds.
            process_names: dict[task_id, worker_id]
                Dict where each entry is the string name for worker with 
                `id=worker_id` assigned to the task with `id=task_id`. 
            metadata -- dict[task_id, worker_id][i] = (job_start, job_finish)
                Dict where each entry is a list of job start/finish times for 
                worker defined above. 
        """

        assert len(process_names) == len(
            metadata), "names and metadata must have same length"
        self._start = start_time
        self._finish = finish_time
        self._names = process_names
        self._meta = metadata


class Diagram:
    """ Parallel Timing Diagram *** come back """

    def __init__(self,
                 *,
                 diagram_spec: DiagramSpec = None,
                 meta_manager: MetadataManager = None):

        assert diagram_spec is not None or meta_manager is not None, "must give a diagram specification or a metadata manager"

        self._start = diagram_spec._start if meta_manager is None else meta_manager._start_time
        self._finish = diagram_spec._finish if meta_manager is None else meta_manager._finish_time
        self._names = diagram_spec._names if meta_manager is None else meta_manager._name_map
        self._meta = diagram_spec._meta if meta_manager is None else meta_manager._meta_map
