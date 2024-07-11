import numpy as np
from screeninfo import get_monitors
from utils.consts import IMAGE_RESIZE_WIDTH, WINDOW_WIDTH, MIN_FRAME_CONTENT_PARTITION, SAME_CONTOUR_THRESHOLD
import os
import pygame
import cv2
import math

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
        """since the size of the image is to be changed based on the rect size, we will set the screen size based on the output"""
        window_height = secondary_monitor.height
        window_width = secondary_monitor.width

        # resize_calc = min((img_h_resized/img_w_resized)/(window_height/window_width), (window_height/window_width)/(img_h_resized/img_w_resized))
        # if resize_calc < SAME_CONTOUR_THRESHOLD:
            # img_w_resized = int(img_h_resized * (window_width/window_height))
            # img_h_resized = int(img_w_resized * (window_height/window_width))

        output_resize_proportion = min(window_height/img_h_resized, window_width/img_w_resized)

        screen_x = secondary_monitor.x
        screen_y = secondary_monitor.y

        flags = pygame.FULLSCREEN

        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{screen_x},{screen_y}"
    else:
        print("Secondary monitor not found")

    window_size = (int(window_width), window_height)
    img_resize = (img_w_resized, img_h_resized)

    # print(window_size, img_resize, window_size[0]/window_size[1], img_resize[0]/img_resize[1])

    return (window_size, img_resize, output_resize_proportion , flags)

def getTransformationMatrix(contours, img_resize, win_size):
    _, appx, _ = findBoard(contours, img_resize)

    avg_pt_appx = (appx[0][0] + appx[1][0] + appx[2][0] + appx[3][0])/4
    first_item = next((i for i, x in enumerate(appx) if x[0][0] < avg_pt_appx[0] and x[0][1] > avg_pt_appx[1]), -1)
    ordered_apps = []
    for i in range(0,4):
        ordered_apps.append(appx[(first_item - i)%4])
    
    # trimmed = []
    # for i in range(0,4):
    #     orig_pt = ordered_apps[i][0]
    #     for j in range(0,2):
    #         if orig_pt[j] < avg_pt_appx[j]: orig_pt[j]-=15
    #         else: orig_pt[j]+=15
    #     trimmed.append(orig_pt)

    # print("trimmed", trimmed)
    
    inp =  np.float32([ordered_apps[0][0], ordered_apps[1][0], ordered_apps[2][0], ordered_apps[3][0]])
    out =  np.float32([[0, win_size[1] - 1], [0,0], [win_size[0] - 1, 0], [win_size[0] - 1, win_size[1] - 1]])

    inp_proportion = getRectProportions(inp)
    out_proportion = getRectProportions(out)

    new = inp

    if min(inp_proportion/out_proportion, out_proportion/inp_proportion) < SAME_CONTOUR_THRESHOLD:
    # after organizing the spots, we can assume inp[0],inp[1] on the left end and inp[2],inp[3] on the right end, therefore x(inp[0],inp[1]) > x(inp[2],inp[3])
        dist_no_change = math.dist(inp[0],inp[1])
        top_proportion = math.dist(inp[1],inp[2]) / (math.dist(inp[3],inp[0]) + math.dist(inp[1],inp[2]))

        new_point_2 = findPointOnLine(inp[1], inp[2], dist_no_change*out_proportion*top_proportion*2)
        new_point_3 = findPointOnLine(inp[0], inp[3], dist_no_change*out_proportion*(1-top_proportion)*2)

        new = (inp[0], inp[1], new_point_2, new_point_3)

    matrix = cv2.getPerspectiveTransform(inp,out)

    return np.array(inp, dtype=np.int32).reshape((-1, 1, 2)), np.array(new, dtype=np.int32).reshape((-1, 1, 2)), matrix
    # return np.array(inp, dtype=np.int32).reshape((-1, 1, 2)), np.array(new, dtype=np.int32).reshape((-1, 1, 2))

def getRectProportions(rect):
    side1 = (math.dist(rect[0],rect[1]) + math.dist(rect[2],rect[3]))/2
    side2 = (math.dist(rect[1],rect[2]) + math.dist(rect[0],rect[3]))/2

    return (side2/side1)

def findPointOnLine(pt1,pt2,dist):
    # a = (pt2[1] - pt1[1])/(pt2[0] - pt1[0])
    # b= pt2[1] - a*pt2[0]
    # # print(f'f(x) = {a}x + {b}')

    # new_x = pt1[0] + (pt2[0]-pt1[0])*dist
    # return (new_x, a*new_x + b)

    direction = pt2 - pt1
    length = np.linalg.norm(direction)
    direction_normalized = direction / length
    scaled_direction = direction_normalized * dist
    point = pt1 + scaled_direction

    # print("DISTANCE: ", math.dist(pt1,point), "vs required: ", dist)

    return point


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
