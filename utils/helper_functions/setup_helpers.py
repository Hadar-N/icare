import os
import sys
import json
import re
import time
import cv2
import numpy as np
from logging import Logger
from enum import Enum
from screeninfo import get_monitors, Monitor

from utils.consts import IMAGE_RESIZE_WIDTH, DEFAULT_WINDOW_WIDTH, CAMERA_RES, CAMERA_SETUP_ATTEMPTS

temp_re = re.compile(r"(?<=\=)\d+\.\d+")
diskspace_re = re.compile(r"[\d.]+(?=%)")

def isVarInEnum(var: str, enum: Enum, is_value: bool = False) -> bool:
    return var and var in [i.value if is_value else i.name for i in enum]

def asstr(arr: np.ndarray | list) -> str:
    return f'[{",".join(asstr(x) if isinstance(x, np.ndarray) else str(x) for x in arr)}]'

def get_pi_temp () -> float:
    t = os.popen('vcgencmd measure_temp').readline()
    match = float(re.search(temp_re, t)[0])
    return match

def followup_temp (logger: Logger, counter: int) -> bool:
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

def get_terminal_params():
    args = sys.argv
    if len(args):
        str = " ".join(args[1:])
        params = json.loads(str)
        coords = np.array(params['coords'])
        win_size = tuple(params['win_size'])
        return coords, win_size
    return None, None

def get_monitor_information(proj_res: str, logger: Logger) -> tuple[Monitor, bool]:
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
        return (None, None)

def get_img_resize_information() -> tuple[int]:
    img_w, img_h = CAMERA_RES
    img_w_resized = IMAGE_RESIZE_WIDTH
    img_h_resized = int(img_h * (img_w_resized/img_w))
    img_size = (int(img_w_resized), int(img_h_resized))
    return img_size

def screen_setup(img_size: tuple, proj_res: str, logger: Logger) -> tuple[tuple, bool]:
    window_width = DEFAULT_WINDOW_WIDTH
    window_height = window_width*(img_size[1]/img_size[0])
    isfullscreen= True

    if proj_res is None:
        isfullscreen = False
    else:
        blah = get_monitor_information(proj_res, logger)
        monitor, is_main = blah
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

def setCameraFunctionAttempt(envval: str, img_resize: tuple[int], logger: Logger = None) -> tuple[callable]:
    for i in range (0, CAMERA_SETUP_ATTEMPTS):
        try:
            takePicture, removeCamera = setCameraFunction(envval, img_resize)

            image = takePicture()
            if image is not None and image.size > 0:
                if logger: logger.info(f'camera initialization succeeded at attempt {i}')
                return takePicture, removeCamera
        except Exception as e:
            if logger: logger.info(f"Camera initialization attempt {i} failed at: {e}")
        time.sleep(2)
    if logger: logger.error(f"Camera initialization failed at attempts")
    raise Exception("Camera initialization failed")

def setCameraFunction(envval: str, img_resize: tuple[int]) -> tuple[callable]:
    takePicture = removeCamera = incResize = None
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
    
    incResize = lambda: cv2.resize(takePicture(), img_resize)

    return incResize, removeCamera
