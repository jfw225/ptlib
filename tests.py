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
                s += f"\n\tReceived: \n\t\t{actual}\n\tExpected: \n\t\t{expected}"

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

@add_test(solutions=[[(5, 2), (3, 3), (3, 3)]])
def job_infer_test_1():
    output_job = pt.core.job.Jobbb()

    subjob1 = output_job[0]
    subjob2 = output_job[5]
    subjob3 = output_job[2]

    subjob1[:] = np.ones((5, 2))

    for i in range(3):
        subjob2[i][:] = [0, 0, 0]

    for i in range(3):
        for j in range(3):
            subjob3[i][j] = 0

    job_spec, input_job = output_job.infer()

    return [tuple(js.shape) for js in job_spec]


# ---------------------------------------------------------------------- #


if __name__ == '__main__':
    if tests is not None:
        tests.run()
