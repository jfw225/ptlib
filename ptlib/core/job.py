from multiprocessing.shared_memory import SharedMemory
import numpy as np

from typing import Iterable, Tuple


class JobSpec(list):
    """ Job specification. *** COME BACK *** """

    def __init__(self,
                 shape: Tuple[int] = None,
                 dtype: np.dtype = None,
                 *, example: np.ndarray = None):
        """
        Parameters:
            shape -- Tuple[int]
                The shape of the data.
            dtype -- np.dtype
                The type of the data.
            example -- ndarray
                An example data to infer structure and space requirements of
                the data (if provided, shape and dtype will be ignored)
        """

        super().__init__([self])

        if example is not None:
            example = np.array(example)
            shape, dtype = example.shape, example.dtype

        self.shape = shape
        self.dtype = dtype

    def __add__(self, x: "JobSpec") -> "JobSpec":
        """
        List is inherited to allow for JobSpec objects to be combined using the
        addition operator `+`.
        """

        return super().__add__(x)

    def __repr__(self):
        return "[" + str(self) + "]"

    def __str__(self):
        return f"Shape: {self.shape}, DType: {self.dtype}"


class Job(np.ndarray):
    """ Job wrapper. *** COME BACK *** """

    def __new__(cls,
                job_specs: JobSpec,
                buffers: Iterable[SharedMemory] = None):

        # create empty array
        job = np.ndarray(len(job_specs), dtype=object)

        # fill array
        for i, job_spec in enumerate(job_specs):
            buf = buffers[i].buf if buffers is not None else None
            job[i] = np.ndarray(shape=job_spec.shape,
                                dtype=job_spec.dtype,
                                buffer=buf)

        return job.view(cls)
