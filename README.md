# Parallel Timing Library

### TODO

- test multiple worker tasks 
- fix queue from overwriting during put
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

- verify that task.id is set properly
- make sure queue works for capacity=1
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

* tests show that ptlib.Queue can be more than 50 times faster than multiprocessing.Queue 
