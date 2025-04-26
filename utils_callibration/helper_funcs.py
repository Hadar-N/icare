import cv2
import numpy as np

from utils import DataSingleton
from utils.consts import THRESHOLD_MAX, MIN_FRAME_CONTENT_PARTITION
from utils.helper_functions import is_pygame_pt_in_contour

global_data = DataSingleton()

def detect_board_auto(image) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresholded = cv2.adaptiveThreshold(gray, THRESHOLD_MAX, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,11,2)
    contours, _ = cv2.findContours(thresholded, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    coordinates = find_board(contours)

    return coordinates

def find_board(conts: tuple) -> np.ndarray:
    rects = []

    fake_contour = np.array([[global_data.img_resize[0] - 1, 0], [0,0], [0, global_data.img_resize[1] - 1],
                             [global_data.img_resize[0] - 1, global_data.img_resize[1] - 1]]).reshape((-1,1,2)).astype(np.int32)
    full_area = cv2.contourArea(fake_contour)
    center_pt = (int(global_data.img_resize[0] / 2), int(global_data.img_resize[1] / 2))
    global_data.threshsize = full_area/MIN_FRAME_CONTENT_PARTITION

    for c in conts:
            epsilon = 0.02 * cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, epsilon, True)
            area= cv2.contourArea(approx)
            if len(approx) == 4 and area > global_data.threshsize and area < full_area*.9:
                rects.append({"cnt": approx, "area": area})

    match len(rects):
            case 0: return fake_contour
            case 1: return rects[0]["cnt"]
            case _: return next((r for r in rects if is_pygame_pt_in_contour(r["cnt"], center_pt)), rects[0])["cnt"]
