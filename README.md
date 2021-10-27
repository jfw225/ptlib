# Parallel Timing Library

### TODO
- create requirements file 
- test multiple worker tasks
- document the code lol
- figure out multi-job outputs
- enumerate empty job

- verify that task.id is set properly

- fix task job map documentation
- create way to specify spec in typing. for ex, job: Job[JobSpec]
- create several objects in _typing

- add in diagram
- don't forget modifications done at the bottom of autoclip
- document meaning of edges, times, and rates in the chart


- *** CHANGE queue to hold selection index until job is done so we dont have to copy data from buffer
- *** have put copy directly to output buffer (this may mean locking down output buffer before task starts)