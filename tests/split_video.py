import os
os.chdir("..")
print(os.getcwd())
import ptlib as pt
import multiprocessing as mp
import numpy as np
import cv2


if __name__ == '__main__':
    from tests.test_tasks import VideoIngest, VideoWrite

    # create pipeline
    pipeline = VideoIngest(num_workers=2) >> VideoWrite(num_workers=2)

    # create and run controller
    controller = pt.Controller(pipeline, 5)
    controller.run()
    controller.graph()
