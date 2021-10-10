"""
Create two tasks:
- video reader and batcher
- video writer
"""
import os
import cv2
import tensorflow as tf

from ptlib.task import Task


class ImageIngest(Task):
    """ Task for ingesting images from a file path. 
    *** improve IO by making copies of video? *** """

    def __init__(self, path, task_number, num_ingests, batch_size):
        self.path = path
        self.task_number = task_number
        self.num_ingests = num_ingests
        self.batch_size = batch_size

        super().__init__()

    def create_map(self):
        # disable GPUs for processes other than predict
        gpus = tf.config.list_physical_devices("GPU")
        tf.config.set_visible_devices([], "GPU")

        # create capture object
        capture = cv2.VideoCapture(self.path)

        # compute task specific start position, stop position, and batch_id
        num_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        start_pos = self.task_number * num_frames // self.num_ingests
        stop_pos = (self.task_number + 1) // self.num_ingests
        batch_id = start_pos // self.batch_size
        print(
            f"ingest: {self.task_number} | start: {start_pos} | stop: {stop_pos} | batch_id: {batch_id}")

        # set the capture object to the start position
        capture.set(cv2.CAP_PROP_POS_FRAMES, start_pos)

        # create range to iterate over
        batch_iter = [0 for _ in range(self.batch_size)]

        def job_map(self, _=None):
            output_batch = list()
            for _ in batch_iter:
                ret, frame = capture.read()

                if not ret or start_pos == stop_pos:
                    capture.release()
                    self.EXIT_FLAG = True

                output_batch.append((start_pos, frame))
                start_pos += 1

            return batch_id, output_batch

        return job_map

    def submit_job(self, _=None):
        pass

    def warmup(self, _=None):
        pass


class VideoWrite(Task):
    """ Task for writing videos to file. """

    def __init__(self, path, output_path):
        self.path = path
        self.output_path = output_path
        super().__init__()

    def create_map(self):
        # disable GPUs for processes other than predict
        gpus = tf.config.list_physical_devices("GPU")
        tf.config.set_visible_devices([], "GPU")

        # create output directories
        clip_name, *_ = os.path.splitext(os.path.basename(self.path))
        output_dir = os.path.join(self.output_path, clip_name + "-clips")
        os.makedirs(output_dir, exist_ok=True)

        # determine fps and resolution of original video
        capture = cv2.VideoCapture(self.path)
        fps = int(capture.get(cv2.CAP_PROP_FPS))
        resolution = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(
            capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        capture.release()

        def job_map(self, job):
            if job is Task.Exit:
                self.EXIT_FLAG = True

            batch_id, batch = job

            path = os.path.join(output_dir, f"{clip_name}-{batch_id}.mp4")
            video = cv2.VideoWriter(
                path, cv2.VideoWriter_fourcc(*"mp4v"), fps, resolution)

            for _, frame in batch:
                video.write(frame)

            video.release()

            return None


if __name__ == '__main__':
    video_path = "C:\\Users\\Owner\\projects\\ptlib\\ptlib\\tests\\testvid.mp4"
