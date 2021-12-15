
class WorkerCreationError(Exception):
    """ 
    Error raised when workers are unable to be created for a task.
    """


class WorkerStartError(Exception):
    """
    Error raised when worker processed are unable to be started for a task. 
    """
