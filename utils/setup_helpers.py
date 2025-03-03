from screeninfo import get_monitors
import os
import cv2
import numpy as np
import re
import math

from utils.consts import IMAGE_RESIZE_WIDTH, DEFAULT_WINDOW_WIDTH, CAMERA_RES

temp_re = re.compile("(?<=\=)\d+\.\d+")
diskspace_re = re.compile("[\d.]+(?=%)")

def asstr(arr):
    return f'[{",".join(asstr(x) if isinstance(x, np.ndarray) else str(x) for x in arr)}]'

def get_pi_temp ():
    t = os.popen('vcgencmd measure_temp').readline()
    match = float(re.search(temp_re, t)[0])
    return match

def followup_temp (logger, counter):
    if (counter%100 == 0):
        temp = get_pi_temp()
        if (temp < 57):
            logger.debug(f'temp: {temp}')
        elif (temp < 65):
            logger.info(f'temp: {temp}')
        elif (temp < 77):
            logger.warning(f'temp: {temp}')
        else:
            logger.critical(f'temp: {temp} ==> program exited')
            return True
    return False

def get_monitor_information(proj_res, logger):
    try:
        monitors = get_monitors()
        monitor = monitors[0]
        is_main = True
        if len(monitors) > 1 and proj_res:
            is_main = False
            monitor = next((m for m in monitors if max(m.width,m.height) == max(map(int,proj_res.split('x'))) and min(m.width,m.height) == min(map(int,proj_res.split('x')))), monitors[1])
        return (monitor, is_main)
    except:
        logger.warning("no monitor found!")
        return None, None

def get_img_resize_information():
    img_w, img_h = CAMERA_RES
    img_w_resized = IMAGE_RESIZE_WIDTH
    img_h_resized = int(img_h * (img_w_resized/img_w))
    img_size = (int(img_w_resized), int(img_h_resized))

    return img_size

def screen_setup(img_size, proj_res, logger):
    window_width = DEFAULT_WINDOW_WIDTH
    window_height = window_width*(img_size[1]/img_size[0])
    isfullscreen= True

    if proj_res is None:
        isfullscreen = False
    else:
        monitor, is_main = get_monitor_information(proj_res, logger)
        if monitor:
            window_width = monitor.width
            window_height = monitor.height
            if not is_main: 
                os.environ['SDL_VIDEO_WINDOW_POS'] = f"{monitor.x},{monitor.y}"
                isfullscreen = False
        else:
            print("No monitor found!!!")

    window_size = (int(window_width), int(window_height))
    return (window_size, isfullscreen)


def sort_points(points):
    points = np.array(points)
    sums = points.sum(axis=1)  # x + y
    diffs = np.diff(points, axis=1)[:, 0]

    sorted_points = np.zeros((4, 2), dtype=np.float32)
    sorted_points[0] = points[np.argmin(sums)]  # Top-left
    sorted_points[1] = points[np.argmax(diffs)]  # Bottom-left
    sorted_points[2] = points[np.argmax(sums)]  # Bottom-right
    sorted_points[3] = points[np.argmin(diffs)]  # Top-right

    if math.dist(sorted_points[0], sorted_points[1]) < math.dist(sorted_points[0], sorted_points[3]):
        sorted_points = [sorted_points[0],sorted_points[3], sorted_points[2], sorted_points[1]]

    return sorted_points


def setCameraFunction(envval):
    takePicture, removeCamera = None, None
    if envval == "pi":
        from picamera2 import Picamera2
        camera = Picamera2()

        config = camera.create_preview_configuration(
            main={"size": CAMERA_RES, "format": "BGR888"},
            buffer_count=2
        )

        camera.configure(config)
        camera.start()
        takePicture = lambda: camera.capture_array()
        removeCamera = lambda: camera.stop()
    elif envval == "pc":
        camera = cv2.VideoCapture(0)
        # ret,image = camera.read()
        # if not ret:
        #     print("Error: Failed to capture image")
        def takePictureFunc():
            _,image = camera.read()
            return image
            
        takePicture = takePictureFunc
        removeCamera = lambda: camera.release()
    else:
        raise Exception(".env value incorrect")
    
    return takePicture, removeCamera


