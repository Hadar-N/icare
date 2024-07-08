import cv2
import pygame
import numpy as np
import utils.consts as consts
from shapecontour import ContourPolygon
from screeninfo import get_monitors
# from shapely.geometry import Polygon
from utils.helpers import getRandomColor
import os
# import tkinter
# os.environ['SDL_VIDEO_FULLSCREEN_DISPLAY'] = '1'

def get_secondary_monitor():
    monitors = get_monitors()
    if len(monitors) > 1:
        return monitors[1]  # Return the second monitor
    return None

cam = cv2.VideoCapture(0)
ret,image = cam.read()

if not ret:
    print("Error: Failed to capture image")

img_h, img_w, _ = image.shape

# Initialize Pygame data
pygame.init()
# 
clock = pygame.time.Clock()

window_width = consts.WINDOW_WIDTH/2
window_height = 0

secondary_monitor = get_secondary_monitor()
if secondary_monitor:
    window_height = secondary_monitor.height
    image_resize_proportion = window_height/img_h
    window_width = int(img_w*image_resize_proportion)
    screen_x = secondary_monitor.x
    screen_y = secondary_monitor.y

    os.environ['SDL_VIDEO_WINDOW_POS'] = f"{screen_x},{screen_y}"
else:
    print("Secondary monitor not found")
    
    image_resize_proportion = window_width/img_w
    window_height = int(img_h*image_resize_proportion)
    screen_x = 0
    screen_y = 0

window_size = (int(window_width), window_height)
window = pygame.display.set_mode(window_size,pygame.FULLSCREEN)

curr_group = pygame.sprite.Group()

#TODO: fix internal black contours
#TODO: change inner sprite location/remove it and add new if changes effect it

def getRandomColor() : return int(np.random.choice(range(256)))

def findInImg(img, arr, curr_group):
    surfaces = pygame.sprite.Group()
    max_elm = len(arr) - 1
    # Iterating through each contour to retrieve coordinates of each shape
    for i, zp in enumerate(reversed(arr)):
        (contour, hirar) = zp
        cnt_area = cv2.contourArea(contour)
        # if i == 0 or len(contour) < MIN_CONTOUR_POINTS or (hirar[HIRAR_LEGEND["NEXT"]] == -1 and hirar[HIRAR_LEGEND["PREV"]] == -1):
        if i == max_elm or cnt_area < consts.MIN_CONTOUR_POINTS:
            continue

        temp_sprite = ContourPolygon(contour)
        prev_spr = isSpriteExistInGroup(curr_group, temp_sprite)
        sim_spr = isSpriteExistInGroup(surfaces, temp_sprite)

        if not sim_spr:
            surfaces.add(temp_sprite if not prev_spr else prev_spr.updateShape(contour))

    
    curr_group.empty()
    curr_group.add(surfaces.sprites())
    surfaces.empty()

def isSpriteExistInGroup(s_group, s_temp):

    for s_i in s_group.sprites():
        if s_temp.rect.colliderect(s_i.rect):
            intersection_area = s_i.mask.overlap_area(s_temp.mask, (s_temp.rect.x - s_i.rect.x, s_temp.rect.y - s_i.rect.y))
            perc = max(intersection_area / s_i.area, intersection_area / s_temp.area)
            if(perc > consts.SAME_CONTOUR_THRESHOLD):
                return s_i
    
    return None


def analyzeImg(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) # Converting to gray image
    blurred_img = cv2.GaussianBlur(gray_image,consts.BLUR_SIZE, 0)
    # edges = cv2.Canny(blurred_img, 50, 150)

    # blurred_img = cv2.medianBlur(gray_image,consts.BLUR_CONST)
    # _, thresh_image = cv2.threshold(blurred_img, THRESHOLD_VAL, THRESHOLD_MAX, cv2.THRESH_BINARY_INV)

    kernel = np.ones((5, 5), np.uint8)
    dialated = cv2.dilate(blurred_img, kernel, iterations=1)
    # eroded = cv2.erode(dialated, kernel, iterations=1)

    thresh_image = cv2.adaptiveThreshold(dialated,consts.THRESHOLD_MAX,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,consts.ADAPTIVE_THRESH_AREA,consts.ADAPTIVE_THRESH_CONST)
    contours, hierarchy = cv2.findContours(thresh_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    return contours, hierarchy

def findBoard(cont):
    rects = []
    i=0
    for contour in contours:
        cnt_area = cv2.contourArea(contour)
        # if i == 0 or len(contour) < MIN_CONTOUR_POINTS or (hirar[HIRAR_LEGEND["NEXT"]] == -1 and hirar[HIRAR_LEGEND["PREV"]] == -1):
        if i == 0 or cnt_area > consts.MIN_CONTOUR_POINTS:
            i+=1
            epsilon = 0.05 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            if len(approx) == 4:
                cv2.drawContours(image, contour, -1, (0,0,255), 3)
                rects.append(approx)

    return rects

# image = cv2.resize(image, (window_width,window_height))
# contours, hierarchy = analyzeImg(image)
# rects = findBoard(contours)
# print(rects)

# Main loop
running = True
while running:
    # Clear the Pygame window
    window.fill((150, 150, 150))

    # Draw the shapes on the frame
    _,image = cam.read()
    image = cv2.resize(image, (window_width,window_height))
    
    contours, hierarchy = analyzeImg(image)
    copy = image.copy()

    findInImg(copy, list(zip(contours, hierarchy[0])), curr_group)
    curr_group.update()
    curr_group.draw(window)

    # image = np.rot90(image)
    # frame_surface = pygame.surfarray.make_surface(image)
    # window.blit(pygame.transform.flip(frame_surface, True, False), (0, 0))

    # Update the Pygame display
    pygame.display.update()
    clock.tick(30)
    
    # Handle Pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

pygame.quit()
cam.release()