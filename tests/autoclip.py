import cv2
import numpy as np

import ptlib as pt


class ImageIngest(pt.Task):
    """
    Task ingests and batches frames from a video. 

    Input Jobs:
        None 

    Output Jobs:
        osj0: int
            ID of current batch.
        osj1: ndarray
            Batch of consecutive images taken from the video.
    """

    # variables here are static
    VIDEO_PATH = "C:\\Users\\Owner\\Videos\\Battlefield 2042 Open Beta\\testvid.mp4"
    BATCH_SIZE = 30 * 5  # fps * duartion in seconds

    def create_map(self, worker, input_job, output_job):
        # create local output subjobs from `output_job`
        # osj1: batch id | osj1:
        osj1 = output_job["images"]

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

        def job_map():
            # worker.output_arr.fill(0)
            osj1.fill(0)
            for i in batch_iter:
                ret, frame = capture.read()

                if not ret or worker.current_pos == stop_pos:
                    capture.release()
                    worker.EXIT_FLAG = True
                    break

                # worker.output_arr[i] = frame
                osj1[i][:] = frame
                worker.current_pos += 1

            worker.batch_id += 1

            # return output_batch
            # return [worker.output_arr]

        return job_map

    def get_total_jobs(self):
        capture = cv2.VideoCapture(self.VIDEO_PATH)
        num_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

        return num_frames
