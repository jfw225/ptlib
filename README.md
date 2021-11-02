# Parallel Timing Library
This library that aims to decrease the latency of shared-memory-based communication between asynchronous processes in Python. The common practice for sharing data between parallel processes is using a Python standard library multiprocessing Queue-like data structure. However, this requires that the data be serialized and transferred over a local socket, leading to a significant bottleneck when dealing with large data structures. I have been able to decrease this latency by leveraging the multiprocessing SharedMemory class added to the standard library with the release of Python 3.8. This addition allows the user to allocate bytes in memory and directly read/write to a buffer without serializing data. As it currently stands, implementing this requires an intimidating amount of familiarity with multiprocessing. I aim to abstract most of the heavy lifting in this library with the hope of increasing the readability and efficiency of asynchronous pipelines.

* tests show that ptlib.Queue can be more than 50 times faster than multiprocessing.Queue.


### TODO

- check if lock is being acquired
- implement option to directly specify job spec

- create requirements file 
- way to implement task order non linear pipelines
- document the code lol
- figure out multi-job outputs
- enumerate empty job
- get rid of unused imports
- convert worker back to inheriting mp.Process
- figure out the best way to specify task __init__

- make basequeue have everything fifoqueue has except for implemented get and put
- remove duplicated code from controller `_set_up_tasks`

- fix task job map documentation
- create way to specify spec in typing. for ex, job: Job[JobSpec]
- create several objects in _typing

- don't forget modifications done at the bottom of autoclip
- document meaning of edges, times, and rates in the chart



- *** CHANGE queue to hold selection index until job is done so we dont have to copy data from buffer
- *** have put copy directly to output buffer (this may mean locking down output buffer before task starts)
- *** maybe implement a lock with arrays
- *** figure out how to guarantee seperate core
- *** try to figure out optimal worker numbers under constraints
- *** instead of having several buffers for several I/O, have one buffer and 
keep track of the offset and number of bytes
- *** add way to enable/disable metadata


