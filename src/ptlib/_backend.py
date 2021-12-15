from time import time_ns

#################### BACKEND CONFIGURATION ####################
"""
This file contains backend configurations for several objects, where 
each class corresponds to the name of a file script in the package. 
"""


class _METADATA:
    JOB_SPEC_EXAMPLES = [[1, 1, 1], [time_ns(), time_ns()]]
    QUEUE_MAX_SIZE = 30


class _DIAGRAM:
    PTD_SPACING = 1.5
    CONSOLE_WIDTH = 100
    TIME_DIV = 1e9          # Nanoseconds
###############################################################
