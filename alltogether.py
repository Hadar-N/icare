import cv2
import pygame
import numpy as np
import utils.consts as consts
from sprites.ContourPolygon import ContourPolygon
from utils.setup_helpers import screenSetup, getTransformationMatrix, originImageResize, calcResizeProportion
from utils.internals_management_helpers import getFishOptions
from utils.dataSingleton import DataSingleton

# image = cv2.imread(consts.IMAGE_PATH)
cam = cv2.VideoCapture(0)
ret,image = cam.read()

if not ret:
    print("Error: Failed to capture image")

global_data = DataSingleton()

win_name = "threshold image"
cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)

# Initialize Pygame data
pygame.init()
clock = pygame.time.Clock()

img_resize = originImageResize(image)
window_size, window_flags = screenSetup(img_resize)
global_data.window_size = window_size
resize_proportion, proportional_image_resize = calcResizeProportion(img_resize, window_size)
window = pygame.display.set_mode(window_size, window_flags)

global_data.fish_options = getFishOptions()
curr_group = pygame.sprite.Group()
    
#TODO: inner shapes only (on board)
#TODO: fix internal black contours
#TODO: change inner sprite location/remove it and add new if changes effect it

def findInImg(arr, curr_group):
    surfaces = pygame.sprite.Group()
    # Iterating through each contour to retrieve coordinates of each shape
    for i, zp in enumerate(reversed(arr)):
        (contour, hirar) = zp
        cnt_area = cv2.contourArea(contour)
        # if i == 0 or len(contour) < MIN_CONTOUR_POINTS or (hirar[HIRAR_LEGEND["NEXT"]] == -1 and hirar[HIRAR_LEGEND["PREV"]] == -1):
        if cnt_area < consts.MIN_CONTOUR_AREA:
            continue

        temp_sprite = ContourPolygon(contour, 1)
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
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred_img = cv2.GaussianBlur(gray_image, consts.BLUR_SIZE, 0)
    kernel = np.ones((5, 5), np.uint8)
    dialated = cv2.dilate(blurred_img, kernel, iterations=1)
    
    cleaned_mask = cv2.morphologyEx(dialated, cv2.MORPH_CLOSE, kernel)
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_OPEN, kernel)

    thresh_image = cv2.adaptiveThreshold(cleaned_mask,consts.THRESHOLD_MAX,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,consts.ADAPTIVE_THRESH_AREA,consts.ADAPTIVE_THRESH_CONST)
    contours, hierarchy = cv2.findContours(thresh_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    return contours, hierarchy


contours, _ = analyzeImg(image)
board_pts, matrix = getTransformationMatrix(contours, img_resize, window_size)

# Main loop
running = True
while running:
    # Clear the Pygame window
    window.fill((0, 0, 0))

    # Draw the shapes on the frame
    _,image = cam.read()
    image = cv2.warpPerspective(image, matrix, window_size ,flags=cv2.INTER_LINEAR)
    
    contours, hierarchy = analyzeImg(image)

    findInImg(list(zip(contours, hierarchy[0])), curr_group)
    curr_group.update()
    curr_group.draw(window)

    [cv2.drawContours(image, sp.contour, -1, sp.contour_color, 2) for sp in curr_group.sprites()]
    cv2.imshow(win_name, image)
    if cv2.waitKey(1) & 0xFF == 27:
        break

    # Update the Pygame display
    pygame.display.update()
    clock.tick(30)
    
    # Handle Pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

pygame.quit()
cam.release()