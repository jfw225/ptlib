from ptlib._typing import Job


class Task:
    """ 
    Template class for making new Task objects. 

    Parameters:
        config -- ptlib.task.config
            Task configuaration object used to set up task at runtime.

    Attributes:
        config -- ptlib.task.config
            Task configuration object passed at runtime.
        EXIT_FLAG -- bool
            Used to determine loop termination in process.
    """

    class Exit:
        pass

    # ---------------------------------------------------------------------- #
    # Constructors

    def __init__(self):
        self.EXIT_FLAG = False

    def submit_job(self, job: Job) -> Job:
        """ 
        Submit `job` to be processed. Within this function, an expression 
        should be evaluated to determine if `self.EXIT_FLAG` needs to be set 
        to true. This function should be overloaded. 
        """

        if job is Task.Exit:
            self.EXIT_FLAG = True

        return job

    def warmup(self, job: Job) -> Job:
        """ 
        Submit job to warmup routine. This function should be overloaded 
        if needed. 
        """

        return job

    def cleanup(self):
        """ 
        Routine for task cleanup after termination. This function should be 
        overloaded if needed. 
        """

        pass
