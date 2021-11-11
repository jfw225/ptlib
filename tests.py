import ptlib as pt

import numpy as np


class TestCase:
    def __init__(self, fn, args, solutions):
        self.fn = fn
        self.args = args
        self.solutions = solutions
        self.next = None
        self.test_id = 0

    def run(self):
        test_case = self
        while test_case is not None:
            solutions = test_case.fn(*test_case.args)
            if isinstance(solutions, tuple):
                solutions = list(solutions)
            else:
                solutions = [solutions]

            test_case.check_solution(solutions)
            test_case = test_case.next

    def check_solution(self, solutions):
        s = "=" * 80 + \
            f"\nTest Case: {self.fn.__name__} | ID: {self.test_id}\n"
        for i, (actual, expected) in enumerate(zip(solutions, self.solutions)):
            s += f"\n\tOutput {i}: "
            if actual == expected:
                s += "correct!"
            else:
                s += f"\n\tReceived: \n{actual}\n\tExpected: \n{expected}"

        s += "\n" + "=" * 80
        print(s)

    def __rshift__(self, other):
        """
        Allows for test cases to be connected with the `>>` operator. 
        """

        if not isinstance(other, TestCase):
            return self

        test_case = self
        while test_case.next is not None:
            test_case = test_case.next

        other.test_id = test_case.test_id + 1
        test_case.next = other

        return self


global tests
tests = None


def add_test(args=list(), solutions=list()):
    """
    Adds a new `TestCase` object to `tests` for function `fn` with paramaters 
    `args` and expected return values `solutions`.
    """

    def wrap(fn):
        global tests

        new_test = TestCase(fn, args, solutions)
        tests = tests >> new_test if tests is not None else new_test

    return wrap


# ---------------------------------------------------------------------- #
# Test Functions

@add_test([5], [6])
def job_infer_test_1(x):
    return np.zeros((3, 3))


# ---------------------------------------------------------------------- #


if __name__ == '__main__':
    if tests is not None:
        tests.run()
