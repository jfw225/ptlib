from multiprocessing.shared_memory import SharedMemory
import numpy as np

from typing import Hashable, Iterable, Tuple


class JobSpec(list):
    """ Job specification. *** COME BACK *** """

    def __init__(self,
                 shape: Tuple[int] = None,
                 dtype: np.dtype = None,
                 *,
                 name: Hashable = None,
                 example: np.ndarray = None):
        """
        Parameters:
            shape -- Tuple[int]
                The shape of the data.
            dtype -- np.dtype
                The type of the data.
            name -- Hashable
                The key that will be used to index the `SubJob` in the `Job`. 
            example -- ndarray
                An example data to infer structure and space requirements of
                the data (if provided, shape and dtype will be ignored)
        """

        super().__init__([self])

        # if no shape nor example is given, assumed to be an empty spec
        self._is_empty = shape is None and example is None
        if self._is_empty:
            return

        self.name = name
        if example is not None:
            example = np.array(example)
            shape, dtype = example.shape, example.dtype

        self.shape = np.array(shape, dtype=np.ulonglong)
        self.dtype = dtype
        self.nbytes = int(np.nbytes[self.dtype] * np.product(self.shape))

    @classmethod
    def from_output_job(cls, output_job: "Job" or np.ndarray):
        """ 
        Alternative constructor for determing job specifications from an 
        instance of `ptlib.core.job.Job`. 
        """

        job_spec_list = [cls(example=job) for job in output_job]

        job_specs = job_spec_list.pop(0)
        for next_job_spec in job_spec_list:
            job_specs += next_job_spec

        return job_specs

    def __add__(self, x: "JobSpec") -> "JobSpec":
        """
        List is inherited to allow for JobSpec objects to be combined using the
        addition operator `+`.
        """

        if self._is_empty:
            return x

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


class Jobb(np.ndarray):
    """
    calculate the total buffer size
    allocate buffer in memory
    link individual arrays using offset and shape

    start with get:
        create a data array size of buffer
        on get, load buffer data into array
        give smaller arrays as the input jobs"""

    def __new__(cls, job_specs: JobSpec):
        """
        Returns job array with buffer. (*** FIX)
        """

        # calculate size of buffer
        nbytes = sum([job_spec.nbytes for job_spec in job_specs])

        # create buffer array (int8 to secure `nbytes`)
        buffer = np.empty(nbytes, dtype=np.int8)

        # create job array
        job = np.ndarray(len(job_specs), dtype=object)

        # fill job array
        job_offset = 0
        for i, job_spec in enumerate(job_specs):
            job[i] = np.ndarray(shape=job_spec.shape,
                                dtype=job_spec.dtype,
                                buffer=buffer,
                                offset=job_offset)
            job_offset += job_spec.nbytes

        return job.view(cls), buffer


class Jobbb(dict):
    """ object used for inferring job structures """

    def __init__(self):
        super().__init__()

        # if dictionary is set-sliced with object v, v is stored in this
        self._subjob = None

    def infer(self):
        """
        Infers the structure of each `SubJob` and returns a `JobSpec` object.
        Calling this function also collapses each embedded `Job` object into 
        a `SubJob`.
        """

        job_spec = JobSpec()
        for key, subjob in self.items():
            if isinstance(subjob, Jobbb):
                subjob = self[key] = subjob.collapse()

            job_spec = job_spec + JobSpec(name=key, example=subjob)

        return job_spec, self

    def collapse(self):
        """
        Recursively collapses embedded `Job` objects into a single numpy 
        array.
        """

        if self._subjob is not None:
            return self._subjob

        subjobs = list()
        for subjob in self.values():
            if isinstance(subjob, Jobbb):
                subjob = subjob.collapse()

            subjobs.append(subjob)

        return np.array(subjobs)

    def __getitem__(self, k):
        print(k)
        if k not in self:
            self[k] = Jobbb()

        return super().__getitem__(k)

    def __setitem__(self, k, v) -> None:
        print(k, v)
        # if `k` is a slice, then
        if not isinstance(k, slice):
            return super().__setitem__(k, v)

        self._subjob = v


def temp(input_job, output_job):
    j1 = input_job[0]

    output_job[0] = 1
