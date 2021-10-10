from ptlib._typing import Job

class Task:
    """ Template class for making new Task objects. """

    # -------------------------------------------------------------------------------- #
    # Constructors

    def __init__(self):
        pass

    def submit_job(self, job: Job) -> Job:
        """ Submit job to be processed. This function should be overloaded. """

        return job

    def is_active(self):
        """ Predicate for terminating process run loop. This function should be overloaded. """

        return False