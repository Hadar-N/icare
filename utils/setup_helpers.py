from screeninfo import get_monitors
import os
import pygame
import cv2
import math
import numpy as np
import re
import time

from utils.dataSingleton import DataSingleton
from utils.consts import IMAGE_RESIZE_WIDTH, DEFAULT_WINDOW_WIDTH, MIN_FRAME_CONTENT_PARTITION, THRESHOLD_VAL, THRESHOLD_MAX, BLUR_SIZE

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
        if (temp < 65):
            logger.info(f'temp: {temp}')
        elif (temp < 77):
            logger.warning(f'temp: {temp}')
        else:
            logger.critical(f'temp: {temp} ==> program exited')
            return True

def setup_window(logger,PROJ_RES, image):
    global_data = DataSingleton()
    pygame.init()
    pygame.font.init()

    img_resize = originImageResize(image)
    global_data.img_resize = img_resize
    window_size, window_flags = screenSetup(img_resize, PROJ_RES, logger)
    global_data.window_size = window_size
    window = pygame.display.set_mode(global_data.window_size, window_flags)

    return window

def setup_img_comparison(window, image, takePicture):
    global_data = DataSingleton()

    image = cv2.resize(image, global_data.img_resize)
    contours = findContours(image)
    inp, out, matrix = getTransformationMatrix(contours, global_data.img_resize, global_data.window_size)

    window.fill((0, 0, 0))
    pygame.display.update()
    time.sleep(2)  # Wait for 2 seconds
    # get darkened reference image
    reference_image = cv2.flip(cv2.warpPerspective(cv2.resize(takePicture(), global_data.img_resize), matrix, (global_data.window_size[1], global_data.window_size[0]) ,flags=cv2.INTER_LINEAR), 0)
    reference_blur = cv2.GaussianBlur(reference_image, BLUR_SIZE, 0)
    threshvalue = findthreshval(reference_blur) * 1.2
    print("threshvalue: ", findthreshval(reference_blur), threshvalue)

    return matrix, threshvalue, reference_blur

def findthreshval(empty_image):
    val = np.mean(np.mean(empty_image, axis=(0,1)), axis=0)
    return val

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

def originImageResize(img):
    img_h, img_w, _ = img.shape
    img_w_resized = IMAGE_RESIZE_WIDTH
    img_h_resized = int(img_h * (img_w_resized/img_w))
    img_size = (int(img_w_resized), int(img_h_resized))

    return img_size

def screenSetup(img_size, proj_res, logger):
    window_width = DEFAULT_WINDOW_WIDTH
    window_height = window_width*(img_size[1]/img_size[0])
    flags = pygame.FULLSCREEN

    monitor, is_main = get_monitor_information(proj_res, logger)
    if monitor:
        window_width = monitor.width
        window_height = monitor.height
        if not is_main: 
            os.environ['SDL_VIDEO_WINDOW_POS'] = f"{monitor.x},{monitor.y}"
            flags = pygame.NOFRAME
    else:
        print("No monitor found!!!")

    window_size = (int(window_width), int(window_height))
    return (window_size, flags)

def findContours(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, THRESHOLD_VAL, THRESHOLD_MAX, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def sortPoints(points):
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

def getTransformationMatrix(contours, img_resize, win_size):
    appx = sortPoints([item[0] for item in findBoard(contours, img_resize)])
    
    inp =  np.float32(appx)
    out =  np.float32([[0,0], [0, win_size[0] - 1], [win_size[1] - 1, win_size[0] - 1], [win_size[1] - 1, 0]])

    matrix = cv2.getPerspectiveTransform(inp, out)

    return inp, out, matrix

def getRectProportions(rect):
    side1 = (math.dist(rect[0],rect[1]) + math.dist(rect[2],rect[3]))/2
    side2 = (math.dist(rect[1],rect[2]) + math.dist(rect[0],rect[3]))/2
    return min(side2/side1, side1/side2)

def findPointOnLine(pt1,pt2,dist):
    direction = pt2 - pt1
    length = np.linalg.norm(direction)
    direction_normalized = direction / length
    scaled_direction = direction_normalized * dist
    point = pt1 + scaled_direction

    return point


def findBoard(conts, img_resize):
    rects = []

    fake_contour = np.array([[img_resize[0] - 1, 0], [0,0], [0, img_resize[1] - 1], [img_resize[0] - 1, img_resize[1] - 1]]).reshape((-1,1,2)).astype(np.int32)
    full_area = cv2.contourArea(fake_contour)
    area_theshold = full_area/MIN_FRAME_CONTENT_PARTITION

    for c in conts:
        epsilon = 0.02 * cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, epsilon, True)
        area= cv2.contourArea(approx)
        if len(approx) == 4 and area > area_theshold and area < full_area:
            rects.append({"cnt": approx, "area": area})

    match len(rects):
        case 0: return fake_contour
        case 1: return rects[0]["cnt"]
        case _: return max(rects, key=lambda c: c["area"])["cnt"]

def setCameraFunction(envval):
    takePicture, removeCamera = None, None
    if envval == "pi":
        from picamera2 import Picamera2
        camera = Picamera2()

        config = camera.create_preview_configuration(
            main={"size": (1640, 1232), "format": "BGR888"},
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


