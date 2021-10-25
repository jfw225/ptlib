import numpy as np
import multiprocessing as mp
from multiprocessing.managers import BaseManager

from ptlib import Task
from ptlib.core.job import JobSpec, Job


class A:
    def __init__(self) -> None:
        print("a")
        super().__init__()


class B:
    def __init__(self) -> None:
        print("b")


class C(A, B):
    def __init__(self) -> None:
        super(C, self).__init__()


class Test():
    def __init__(self):
        self.a = np.zeros(0)
        self.b = np.zeros(2)

    def func(self):
        for arr in [self.a.__name__, self.b.__name__]:
            print(arr)
            # arr = np.ones(5)

    def __str__(self) -> str:
        return "test"


if __name__ == '__main__':
    # c = C()
    # _name = str(c.__class__)
    # name = _name[_name.find(".") + 1:].rstrip("'>")

    k = JobSpec((5,), dtype=np.int)
    j = Job(k)
    print(type(j[0]), type(j), j[:].shape)
    print(j)
    # j[:][:] = np.array([[1, 2, 3, 4, 5]])[:][:]

    print(j)

    inp = np.ndarray((1, 2), dtype=object)
    print(inp)
    inp[0]

    print(k + k)
    print(sum([k, k]))
