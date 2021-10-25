import multiprocessing as mp
from multiprocessing.managers import BaseManager

from ptlib import Task


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


class Test(BaseManager):
    def __init__(self):
        super().__init__(("localhost", 64531))

        mp.Process(target=self.get_server().serve_forever, daemon=True).start()


if __name__ == '__main__':
    # c = C()
    # _name = str(c.__class__)
    # name = _name[_name.find(".") + 1:].rstrip("'>")

    t = Test()
