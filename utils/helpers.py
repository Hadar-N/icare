import numpy as np
from screeninfo import get_monitors
from utils.consts import IMAGE_RESIZE_WIDTH, WINDOW_WIDTH, MIN_FRAME_CONTENT_PARTITION
import os
import pygame
import cv2

def getRandomColor() : return int(np.random.choice(range(256)))

def get_secondary_monitor():
    monitors = get_monitors()
    if len(monitors) > 1:
        return monitors[1]  # Return the second monitor
    return None


def screenSetup(img):
    img_h, img_w, _ = img.shape
    img_w_resized = IMAGE_RESIZE_WIDTH
    img_resized_proportion = img_w_resized/img_w
    img_h_resized = int(img_h * img_resized_proportion)

    window_width = WINDOW_WIDTH
    output_resize_proportion = window_width/img_w_resized
    window_height = img_h_resized*output_resize_proportion
    screen_x = 0
    screen_y = 0

    flags= 0

    secondary_monitor = get_secondary_monitor()
    if secondary_monitor:
        window_height = secondary_monitor.height
        output_resize_proportion = window_height/img_h_resized
        window_width = int(img_w_resized*output_resize_proportion)

        if (window_width > secondary_monitor.width):
            window_width = secondary_monitor.width
            output_resize_proportion = window_width/img_w_resized
            window_height = int(img_h_resized*output_resize_proportion)

        screen_x = secondary_monitor.x
        screen_y = secondary_monitor.y

        flags = pygame.FULLSCREEN

        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{screen_x},{screen_y}"
    else:
        print("Secondary monitor not found")

    window_size = (int(window_width), window_height)
    img_resize = (img_w_resized, int(img_h_resized))

    return (window_size, img_resize, output_resize_proportion , flags)

def getTransformationMatrix(contours, img_resize):
    _, appx, _ = findBoard(contours, img_resize)

    avg_pt_appx = (appx[0][0] + appx[1][0] + appx[2][0] + appx[3][0])/4
    first_item = next((i for i, x in enumerate(appx) if x[0][0] > avg_pt_appx[0] and x[0][1] < avg_pt_appx[0]), -1)
    ordered_apps = []
    for i in range(0,4):
        ordered_apps.append(appx[(first_item + i)%4])
    
    inp =  np.float32([ordered_apps[0][0], ordered_apps[1][0], ordered_apps[2][0], ordered_apps[3][0]])
    out =  np.float32([[img_resize[0] - 1, 0], [0,0], [0, img_resize[1] - 1], [img_resize[0] - 1, img_resize[1] - 1]])

    matrix = cv2.getPerspectiveTransform(inp,out)

    return matrix


def findBoard(conts, img_resize):
    rects = []
    fake_contour = np.array([[img_resize[0] - 1, 0], [0,0], [0, img_resize[1] - 1], [img_resize[0] - 1, img_resize[1] - 1]]).reshape((-1,1,2)).astype(np.int32)
    full_area = cv2.contourArea(fake_contour)
    area_theshold = full_area/MIN_FRAME_CONTENT_PARTITION

    for contour in conts:
        cnt_area = cv2.contourArea(contour)
        if cnt_area > area_theshold and cnt_area < full_area:
            epsilon = 0.05 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            if len(approx) == 4:
                rects.append((cnt_area, approx, contour))

    if len(rects) == 0:
        return (full_area, fake_contour, fake_contour)
    if len(rects) == 1: return rects[0]
    else:
        return max(rects, key=lambda r: r[0])
