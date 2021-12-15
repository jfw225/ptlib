import cv2
import pickle
import numpy as np

import ptlib as pt
from ptlib.core.metadata import MetadataManager
from ptlib.core.queue import Queue


class VideoIngest(pt.Task):
    # variables here are static
    NUM_WORKERS = 1

    VIDEO_PATH = "C:\\Users\\Owner\\Videos\\Battlefield 2042 Open Beta\\testvid.mp4"
    BATCH_SIZE = 30 * 5  # fps * duartion in seconds

    def __init__(self):
        # maybe no init
        super().__init__(num_workers=VideoIngest.NUM_WORKERS)

    def create_map(self, worker):
        # create capture object
        capture = cv2.VideoCapture(self.VIDEO_PATH)

        # compute task specific start position, stop position, and batch_id
        num_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        start_pos = worker.id * num_frames // self.num_workers
        stop_pos = (worker.id + 1) * num_frames // self.num_workers
        worker.batch_id = start_pos // self.BATCH_SIZE
        print(
            f"ingest: {worker.id} | start: {start_pos} | stop: {stop_pos} | batch_id: {worker.batch_id}")

        # get shape and dtype
        _, frame = capture.read()
        shape, dtype = frame.shape, frame.dtype

        # set the capture object to the start position
        capture.set(cv2.CAP_PROP_POS_FRAMES, start_pos)

        # create range to iterate over
        batch_iter = [i for i in range(self.BATCH_SIZE)]

        # set the current frame position
        worker.current_pos = start_pos

        # set zero array and output array
        worker.output_arr = np.zeros((self.BATCH_SIZE, *shape), dtype=dtype)

        def job_map(input_job):
            worker.output_arr.fill(0)
            for i in batch_iter:
                ret, frame = capture.read()

                if not ret or worker.current_pos == stop_pos:
                    capture.release()
                    worker.EXIT_FLAG = True
                    break

                worker.output_arr[i] = frame
                worker.current_pos += 1

            worker.batch_id += 1

            # return output_batch
            return [worker.output_arr]

        return job_map


##### pseudo-controller implementation for testing #####
def run(pipeline, meta_manager, output_q):
    # link output queue
    output_q._link_mem(create_local=True)

    # set start time
    meta_manager.set_time()

    # start all worker processes
    for task in pipeline.iter_tasks():
        task._start_workers()

    task = pipeline
    while task is not pt.EmptyTask:
        # force pull from output queue
        output_q.get()

        # update metadata
        meta_manager.update()

        # if current task finishes, send kill signal to workers
        if not task._workers_running():
            print(f"Task Finished: {task.name}")
            task = task.next
            task._kill_workers()

    # finish retreiving metadata (in case loop exits before getting all metadata)
    meta_manager.update()

    # set finish time
    meta_manager.set_time()


if __name__ == '__main__':
    # create pipeline
    pipeline = VideoIngest()

    # infer output
    output_job, job_specs = pipeline.infer_structure(None)

    # create I/O queues
    input_q, output_q = Queue(), Queue(job_specs, capacity=5)

    # create metadata manager
    meta_manager = MetadataManager(pipeline)

    # create workers and assign them to task
    pipeline.create_workers(input_q, output_q, meta_manager.meta_q)

    # start pseudo-controller
    run(pipeline, meta_manager, output_q)

    # create and run controller
    # controller = pt.Controller(pipeline, 5)
    # controller.run()
    # controller.graph()
