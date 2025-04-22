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
from utils.data_singleton import DataSingleton

global_data = DataSingleton()

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

def followup_temp (counter: int) -> bool:
    if (counter%100 == 0):
        temp = get_pi_temp()
        if (temp < 57):
            global_data.logger.debug(f'temp: {temp}')
        elif (temp < 65):
            global_data.logger.info(f'temp: {temp}')
        elif (temp < 77):
            global_data.logger.warning(f'temp: {temp}')
        else:
            global_data.logger.critical(f'temp: {temp} ==> program exited')
            return True
    return False

def get_terminal_params() -> tuple[np.array, tuple]:
    args = sys.argv
    if len(args):
        str_params = " ".join(args[1:])
        global_data.logger.info(f'received params: {str_params} of type {type(str_params)}')
        params = json.loads(str_params)
        coords = np.array(params['coords'])
        win_size = tuple(params['win_size'])
        return coords, win_size
    return None, None

def get_monitor_information(proj_res: str) -> tuple[Monitor, bool]:
    try:
        monitors = get_monitors()
        monitor = monitors[0]
        is_main = True
        if len(monitors) > 1 and proj_res:
            is_main = False
            monitor = next((m for m in monitors if max(m.width,m.height) == max(map(int,proj_res.split('x'))) and min(m.width,m.height) == min(map(int,proj_res.split('x')))), monitors[1])
        return (monitor, is_main)
    except:
        global_data.logger.warning("no monitor found!")
        return (None, None)

def get_img_resize_information() -> tuple[int]:
    img_w, img_h = CAMERA_RES
    img_w_resized = IMAGE_RESIZE_WIDTH
    img_h_resized = int(img_h * (img_w_resized/img_w))
    img_size = (int(img_w_resized), int(img_h_resized))
    return img_size

def screen_setup(proj_res: str) -> tuple[tuple, bool]:
    window_width = DEFAULT_WINDOW_WIDTH
    window_height = window_width*(global_data.img_resize[1]/global_data.img_resize[0])
    isfullscreen= True

    if proj_res is None:
        isfullscreen = False
    else:
        blah = get_monitor_information(proj_res)
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

def setCameraFunctionAttempt(img_size: tuple[int] = None) -> tuple[callable]:
    if not img_size: img_size = global_data.img_resize
    for i in range (0, CAMERA_SETUP_ATTEMPTS):
        try:
            takePicture, removeCamera = _setCameraFunction(img_size)

            image = takePicture()
            if image is not None and image.size > 0:
                if global_data.logger: global_data.logger.info(f'camera initialization succeeded at attempt {i}')
                return takePicture, removeCamera
        except Exception as e:
            if global_data.logger: global_data.logger.info(f"Camera initialization attempt {i} failed at: {e}")
        time.sleep(2)
    if global_data.logger: global_data.logger.error(f"Camera initialization failed at attempts")
    raise Exception("Camera initialization failed")

def _setCameraFunction(img_size: tuple[int] = global_data.img_resize) -> tuple[callable]:
    takePicture = removeCamera = incResize = None
    if global_data.env == "pi":
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
    elif global_data.env == "pc":
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
    
    incResize = lambda: cv2.resize(takePicture(), img_size)

    return incResize, removeCamera
