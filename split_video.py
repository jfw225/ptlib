"""
Create two tasks:
- video reader and batcher
- video writer
"""
import os
import cv2
import tensorflow as tf
import multiprocessing as mp

import ptlib as pt


class VideoIngest(pt.task.Task):
    """ Task for ingesting images from a file path. 
    *** improve IO by making copies of video? *** """

    def __init__(self, video_path, task_num, num_ingests, batch_size):
        self.video_path = video_path
        self.task_num = task_num
        self.num_ingests = num_ingests
        self.batch_size = batch_size
        self.current_pos = 0
        self.batch_id = 0

        super().__init__()

    def create_map(self):
        # disable GPUs for processes other than predict
        # gpus = tf.config.list_physical_devices("GPU")
        # tf.config.set_visible_devices([], "GPU")

        # create capture object
        capture = cv2.VideoCapture(self.video_path)

        # compute task specific start position, stop position, and batch_id
        num_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        start_pos = self.task_num * num_frames // self.num_ingests
        stop_pos = (self.task_num + 1) * num_frames // self.num_ingests
        self.batch_id = start_pos // self.batch_size
        print(
            f"ingest: {self.task_num} | start: {start_pos} | stop: {stop_pos} | batch_id: {self.batch_id}")

        # set the capture object to the start position
        capture.set(cv2.CAP_PROP_POS_FRAMES, start_pos)

        # create range to iterate over
        batch_iter = [0 for _ in range(self.batch_size)]

        # set the current frame position
        self.current_pos = start_pos

        def job_map(_=None):
            output_batch = list()
            for _ in batch_iter:
                ret, frame = capture.read()

                if not ret or self.current_pos == stop_pos:
                    capture.release()
                    self.EXIT_FLAG = True

                output_batch.append((self.current_pos, frame))
                self.current_pos += 1

            self.batch_id += 1

            return self.batch_id - 1, output_batch

        return job_map

    def submit_job(self, _=None):
        pass

    def warmup(self, _=None):
        pass


class VideoWrite(pt.task.Task):
    """ Task for writing videos to file. """

    def __init__(self, video_path, output_path):
        self.video_path = video_path
        self.output_path = output_path
        super().__init__()

    def create_map(self):
        # disable GPUs for processes other than predict
        # gpus = tf.config.list_physical_devices("GPU")
        # tf.config.set_visible_devices([], "GPU")

        # create output directories
        clip_name, *_ = os.path.splitext(os.path.basename(self.video_path))
        output_dir = os.path.join(self.output_path, clip_name + "-clips")
        os.makedirs(output_dir, exist_ok=True)

        # determine fps and resolution of original video
        capture = cv2.VideoCapture(self.video_path)
        fps = int(capture.get(cv2.CAP_PROP_FPS))
        resolution = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(
            capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        capture.release()

        def job_map(job):
            if job is pt.task.Task.Exit:
                self.EXIT_FLAG = True
                return None

            batch_id, batch = job

            path = os.path.join(output_dir, f"{clip_name}-{batch_id}.mp4")
            video = cv2.VideoWriter(
                path, cv2.VideoWriter_fourcc(*"mp4v"), fps, resolution)

            for _, frame in batch:
                video.write(frame)

            video.release()

            return None

        return job_map


if __name__ == '__main__':
    mp.set_start_method("spawn", force=True)
    # video_path = "test_vid.ts"
    video_path = "C:\\Users\\Owner\\Videos\\Battlefield 2042 Open Beta\\testvid.mp4"
    clip_duration = 5  # 30 seconds
    batch_size = 30 * clip_duration  # fps * duration

    viding_config = pt.task.Config(
        video_path=video_path, task_num=0, num_ingests=1, batch_size=batch_size)
    vidwrite_config = pt.task.Config(
        video_path=video_path, output_path="output/")

    controller = pt.Controller([VideoIngest, VideoWrite], [
                               viding_config, vidwrite_config])
    controller.run()

    # viding_to_vidwrite = mp.Queue()

    # viding_p = pt.Process(VideoIngest, viding_config,
    #                       pt.Queue(fake=True), viding_to_vidwrite)
    # vidwrite_p = pt.Process(VideoWrite, vidwrite_config,
    #                         viding_to_vidwrite, pt.Queue(fake=True))

    # viding_p.start()
    # vidwrite_p.start()

    # while viding_p.is_alive() or vidwrite_p.is_alive():
    #     pass
    # print("done")

    # viding = VideoIngest(**viding_config)
    # vidwrite = VideoWrite(**vidwrite_config)

    # viding_map = viding.create_map()
    # vidwrite_map = vidwrite.create_map()

    # while not viding.EXIT_FLAG:
    #     batch = viding_map()
    #     vidwrite_map(batch)