import cv2
import pygame
import numpy as np
# from PIL import Image
import utils.consts as consts
from utils.helpers import *
from shapecontour import ContourPolygon

# Load image using OpenCV
image = cv2.imread(consts.IMAGE_PATH)
img_h, img_w, _ = image.shape
image_resize_proportion = (consts.WINDOW_WIDTH/2)/img_w
window_height = int(img_h*image_resize_proportion)

# Initialize Pygame data
pygame.init()
window_size = (consts.WINDOW_WIDTH, window_height)
clock = pygame.time.Clock()
window = pygame.display.set_mode(window_size, pygame.RESIZABLE)
curr_group = pygame.sprite.Group()

def findInImg(img, arr, curr_group):
    surfaces = pygame.sprite.Group()
    max_elm = len(arr) - 1
    # Iterating through each contour to retrieve coordinates of each shape
    for i, zp in enumerate(reversed(arr)):
        (contour, hirar) = zp

        # if i == 0 or len(contour) < MIN_CONTOUR_POINTS or (hirar[HIRAR_LEGEND["NEXT"]] == -1 and hirar[HIRAR_LEGEND["PREV"]] == -1):
        if i == max_elm or PolygonArea(contour) < consts.MIN_CONTOUR_POINTS:
            continue

        bounding = cv2.boundingRect(contour)

        prev_cont = isContourExistInGroup(curr_group, bounding)
        sim_cont = isContourExistInGroup(surfaces, bounding)

        if not sim_cont:
            surfaces.add(ContourPolygon(contour, bounding) if not prev_cont else prev_cont.updateShape(contour, bounding))
    
    curr_group.empty()
    curr_group.add(surfaces.sprites())
    surfaces.empty()

# def makeContourIntoShape(img, cnt, bounding, existing):

#     return ContourPolygon(cnt, bounding, color_tmp) if not existing else existing.updateShape(cnt, bounding)

def isContourExistInGroup(s_group, c_bound):
    relevant = next((item for item in s_group.sprites() if isSameContours(item, c_bound)), None)
    if (relevant):
        return relevant
    
    return False

def isSameContours(s_item, c_bound):
    location_same = abs(s_item.rect.x - c_bound[consts.BOUND_LEGEND["X"]]) < consts.COMPARISON_VALUE and abs(s_item.rect.y - c_bound[consts.BOUND_LEGEND["Y"]]) < consts.COMPARISON_VALUE
    size_same = abs(s_item.rect.height - c_bound[consts.BOUND_LEGEND["HEIGHT"]]) < consts.COMPARISON_VALUE*2 and abs(s_item.rect.width - c_bound[consts.BOUND_LEGEND["WIDTH"]]) < consts.COMPARISON_VALUE*2
    return location_same and size_same

def analyzeImg(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) # Converting to gray image
    blurred_img = cv2.GaussianBlur(gray_image,consts.BLUR_SIZE, 0)
    # blurred_img = cv2.medianBlur(gray_image,consts.BLUR_CONST)
    # _, thresh_image = cv2.threshold(blurred_img, THRESHOLD_VAL, THRESHOLD_MAX, cv2.THRESH_BINARY_INV)
    thresh_image = cv2.adaptiveThreshold(blurred_img,consts.THRESHOLD_MAX,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,consts.ADAPTIVE_THRESH_AREA,consts.ADAPTIVE_THRESH_CONST)
    # contours, hierarchy = cv2.findContours(thresh_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    contours, hierarchy = cv2.findContours(thresh_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    return contours, hierarchy

image = cv2.resize(image, (int(consts.WINDOW_WIDTH/2),window_height))
contours, hierarchy = analyzeImg(image)
# Main loop
running = True
while running:
    # Clear the Pygame window
    window.fill((150, 150, 150))


    # Draw the shapes on the frame
    # image = cv2.resize(image, (int(consts.WINDOW_WIDTH/2),window_height))
    copy = image.copy()

    # contours, hierarchy = analyzeImg(image)
    findInImg(copy, list(zip(contours, hierarchy[0])), curr_group)
    curr_group.update()
    curr_group.draw(window)

    copy = np.rot90(copy)
    frame_surface = pygame.surfarray.make_surface(copy)
    window.blit(pygame.transform.flip(frame_surface, True, False), (consts.WINDOW_WIDTH/2, 0))

    # for point in frame_mask.outline():
    #     x = point[0]
    #     y = point[1]
    #     pygame.draw.circle(window,'red',(x,y),1)

    # Update the Pygame display
    pygame.display.update()
    clock.tick(30)
    
    # Handle Pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

pygame.quit()
