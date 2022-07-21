# Parallel Timing Library
This library that aims to decrease the latency of shared-memory-based communication between asynchronous processes in Python. The common practice for sharing data between parallel processes is using a Python standard library multiprocessing Queue-like data structure. However, this requires that the data be serialized and transferred over a local socket, leading to a significant bottleneck when dealing with large data structures. I have been able to decrease this latency by leveraging the multiprocessing SharedMemory class added to the standard library with the release of Python 3.8. This addition allows the user to allocate bytes in memory and directly read/write to a buffer without serializing data. As it currently stands, implementing this requires an intimidating amount of familiarity with multiprocessing. I aim to abstract most of the heavy lifting in this library with the hope of increasing the readability and efficiency of asynchronous pipelines.

* tests show that ptlib.Queue can be more than 50 times faster than multiprocessing.Queue.



