import os
import cv2
import numpy as np
import multiprocessing as mp

import ptlib as pt


if __name__ == '__main__':
    from test_tasks import VideoIngest, VideoWrite

    # create pipeline
    pipeline = VideoIngest(num_workers=2) >> VideoWrite(num_workers=2)

    # create and run controller
    controller = pt.Controller(pipeline, 5)
    controller.run()
    controller.graph()
