# Parallel Timing Library

### TODO
- figure out how to communicate to sub tasks
- document the code lol
- enumerate job structure
- figure out multi-job outputs
- enumerate empty job
- add in timing diagram
- overload manager class of multiprocessing for controller such that 
  more stuff is done in Run Loop

- verify that task.id is set properly
- try sharing objects with proxies or figure out different way to communicate metadata
- figure out how to get from meta queue and figure out which worker

- have multiple job specs
- use the input buffers for output too since the output queue also makes their own buffers

- have job map functions take in the output buffer
- have queue get return True instead of list
- create jobs class to replace input buffers
- fix task job map documentation