from multiprocessing.shared_memory import SharedMemory
import numpy as np

from typing import Hashable, Iterable, Tuple, Any

from numpy.lib.arraysetops import isin


class JobSpec:
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

        self.next = None

        # if no shape nor example is given, assumed to be an empty spec
        self._is_empty = shape is None and example is None
        if self._is_empty:
            self.shape = (0,)
            self.dtype = None
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

    def get_nbytes(self, capacity: int = 1):
        """
        Calculates the number of bytes required to allocate a `ptlib.Job` 
        specified by `self` in a `ptlib.Queue` of size `capacity`. 
        """

        return capacity * sum([js.nbytes for js in self])

    def __iter__(self):
        js = self
        while js is not None:
            yield js
            js = js.next

    def __add__(self, other_js: "JobSpec") -> "JobSpec":
        """
        LinkedList implementation allows for JobSpec objects to be combined 
        using the addition operator `+`.
        """

        if not isinstance(other_js, JobSpec):
            return self

        if self._is_empty:
            return other_js

        js = self
        while js.next is not None:
            js = js.next

        js.next = other_js

        return self

    def __repr__(self):
        return "[" + str(self) + "]"

    def __str__(self):
        s = " | ".join(
            [f"Name: {js.name}, Shape: {js.shape}, DType: {js.dtype}" for js in self])

        return "[" + s + "]"


class Job(dict):
    """ 
    The Job object. Can be used to infer structure of jobs and as a job 
    itself.
    """

    def __init__(self, job_spec: JobSpec = None):
        super().__init__()

        # if no job spec is passed, then this instance is used for inferance
        if job_spec is None:
            # if dictionary is set-sliced with object v, v is stored in this
            self._subjob = None
            return

        # create local buffer for entire job
        self._buffer = np.ndarray(job_spec.get_nbytes(), dtype=np.int8)

        # create subjobs
        offset = 0
        for js in job_spec:
            self[js.name] = np.ndarray(shape=js.shape,
                                       dtype=js.dtype,
                                       buffer=self._buffer,
                                       offset=offset)

            offset += js.nbytes

    def infer(self):
        """
        Infers the structure of each `SubJob` and returns a `JobSpec` object.
        Calling this function also collapses each embedded `Job` object into 
        a `SubJob`.
        """

        job_spec = JobSpec()
        for key, subjob in self.items():
            if isinstance(subjob, Job):
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
            if isinstance(subjob, Job):
                subjob = subjob.collapse()

            subjobs.append(subjob)

        return np.array(subjobs)

    def __getitem__(self, k):
        # print(k)
        if k not in self:
            self[k] = Job()

        return super().__getitem__(k)

    def __setitem__(self, k, v) -> None:
        # print(k, v)
        # if `k` is a slice, then
        if not isinstance(k, slice):
            return super().__setitem__(k, v)

        self._subjob = v

    def __getattribute__(self, __name: str):
        """
        Overloaded to ensure that inferencing of job structure is not stopped 
        due to a method call that does not pertain to the structure. For 
        example, if `subjob1.fill(0)` is called (where `fill` is a method of a 
        `numpy.ndarray`), we want to continue to infer the structure of the 
        subjob without throwing an error. 
        """

        try:
            return super().__getattribute__(__name)
        except AttributeError:
            return Job()

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        """
        Overloaded to protect runtime interruption during structure inference. 
        """

        try:
            return super().__call__(*args, **kwds)
        except TypeError and AttributeError:
            return None
