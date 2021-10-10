"""
Create two tasks:
- video reader and batcher
- video writer
"""

from ptlib import Task


class ImageIngest(Task):
    """ Task for ingesting images from a file path. """

    def __init__(self):
        super().__init__()

    def submit_job(self, _=None):
        pass

    def warmup(self, _=None):
        pass


def image_input(output_q, iminp_id, num_inputs, ptp_id):
    ptp = PTProcess(f"image input: {iminp_id}", ptp_id)

    # Disable GPUs for processes other than predict
    gpus = tf.config.list_physical_devices("GPU")
    tf.config.set_visible_devices([], "GPU")

    cap = cv2.VideoCapture(VIDEO_PATH)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    start = iminp_id * frames // num_inputs
    stop = (iminp_id + 1) * frames // num_inputs
    batch_id = start // BATCH_SIZE
    print(
        f"image input: {iminp_id} | start: {start} | stop: {stop} | batch_id: {batch_id}")
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)

    working = True
    ptp.start()
    while working:
        ptp.on()
        output_batch = list()
        for _ in range(BATCH_SIZE):
            ret, frame = cap.read()

            if not ret or start == stop:
                cap.release()
                working = False
                break

            output_batch.append((start, frame))
            start += 1

        if len(output_batch) > 0:
            # print(ptp._name, batch_id, start)
            ref = ray.put((batch_id, output_batch))
            ptp.off()
            output_q.put(ref)
            batch_id += 1

    ptp.off()
    print(ptp._name + " done")


def video_write(input_q, ptp_id):
    ptp = PTProcess(f"video writer: {ptp_id}", ptp_id)

    # Disable GPUs for processes other than predict
    gpus = tf.config.list_physical_devices("GPU")
    tf.config.set_visible_devices([], "GPU")

    # Output Directories
    clip_name = os.path.splitext(os.path.basename(VIDEO_PATH))[0]
    pos_output_dir = os.path.join(OUTPUT_PATH, clip_name + "-pos")
    neg_output_dir = os.path.join(OUTPUT_PATH, clip_name + "-neg")
    os.makedirs(pos_output_dir, exist_ok=True)
    os.makedirs(neg_output_dir, exist_ok=True)

    cap = cv2.VideoCapture(VIDEO_PATH)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    resolution = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    ptp.start()
    while True:
        try:
            data = input_q.get(block=False)
        except Empty:
            continue

        ptp.on()

        if data == Pipeline.Exit:
            break

        batch_id, batch, is_pos = data

        output_dir = pos_output_dir if is_pos else neg_output_dir
        path = os.path.join(output_dir, f"{clip_name}-{batch_id}.mp4")
        video = cv2.VideoWriter(
            path, cv2.VideoWriter_fourcc(*"mp4v"), fps, resolution)

        for _, frame, _ in batch:
            video.write(frame)

        video.release()
        ptp.off()

    ptp.off()
    print(ptp._name + " done")
