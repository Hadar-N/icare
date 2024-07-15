import cv2
import pygame
import numpy as np
import utils.consts as consts
from shapecontour import ContourPolygon, BigMask, InternalSprite
from utils.helpers import screenSetup, getTransformationMatrix, originImageResize, calcResizeProportion
from random import randint

# image = cv2.imread(consts.IMAGE_PATH)
cam = cv2.VideoCapture(0)
# cam.set(cv2.CAP_PROP_CONVERT_RGB , 0 )
ret,image = cam.read()

if not ret:
    print("Error: Failed to capture image")

# Initialize Pygame data
pygame.init()
clock = pygame.time.Clock()

img_resize = originImageResize(image)
window_size, window_flags = screenSetup(img_resize)
resize_proportion, proportional_image_resize = calcResizeProportion(img_resize, window_size)
window = pygame.display.set_mode(window_size, window_flags)

curr_group = pygame.sprite.Group()
big_mask = pygame.sprite.GroupSingle(BigMask(window_size, 1))
big_surface = pygame.Surface(window_size)
internals = pygame.sprite.Group()

last_pictures = []
    
#TODO: inner shapes only (on board)
#TODO: fix internal black contours
#TODO: change inner sprite location/remove it and add new if changes effect it

# Function to capture the last x images and compute their average
# def capture_and_average_images(images):
#     avg_image = np.mean(images, axis=0).astype(np.uint8)
#     return avg_image

def findInImg(arr, curr_group):
    cntrs = []
    surfaces = pygame.sprite.Group()
    max_elm = len(arr) - 1
    # Iterating through each contour to retrieve coordinates of each shape
    for i, zp in enumerate(reversed(arr)):
        (contour, hirar) = zp
        cnt_area = cv2.contourArea(contour)
        # if i == 0 or len(contour) < MIN_CONTOUR_POINTS or (hirar[HIRAR_LEGEND["NEXT"]] == -1 and hirar[HIRAR_LEGEND["PREV"]] == -1):
        if i == max_elm or cnt_area < consts.MIN_CONTOUR_POINTS:
            continue

        temp_sprite = ContourPolygon(contour, 1)
        sim_spr = isSpriteExistInGroup(surfaces, temp_sprite)

        if not sim_spr:
            cntrs.append(contour)
    
    surfaces.empty()
    big_mask.update(cntrs)

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
    
    thresh_image = cv2.adaptiveThreshold(dialated,consts.THRESHOLD_MAX,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,consts.ADAPTIVE_THRESH_AREA,consts.ADAPTIVE_THRESH_CONST)
    cleaned_mask = cv2.morphologyEx(thresh_image, cv2.MORPH_OPEN, kernel)

    contours, hierarchy = cv2.findContours(cleaned_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    return contours, hierarchy

def analyzepictures(reference_blurred, current_image):
    # reference_blurred = cv2.GaussianBlur(reference_blurred, consts.BLUR_SIZE, 0)
    gray_image = cv2.cvtColor(current_image, cv2.COLOR_BGR2GRAY)
    current_blurred = cv2.GaussianBlur(gray_image, consts.BLUR_SIZE, 0)

    # Compute absolute difference between the current image and the reference image
    difference = cv2.absdiff(current_blurred, reference_blurred)

    # Apply a custom threshold to highlight darkened areas
    _, thresholded = cv2.threshold(difference, 50, 255, cv2.THRESH_BINARY_INV)

    # Perform morphological operations to fill in gaps
    kernel = np.ones((11, 11), np.uint8)  # Larger kernel for more aggressive closing
    closed = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, kernel)

    return closed

contours, _ = analyzeImg(image)
matrix = getTransformationMatrix(contours, img_resize, window_size)
reference_image = cv2.warpPerspective(image, matrix, window_size ,flags=cv2.INTER_LINEAR)
# gray_reference = cv2.cvtColor(reference_image, cv2.COLOR_BGR2GRAY)
reference_blur = cv2.GaussianBlur(reference_image, consts.BLUR_SIZE, 0)

internals = pygame.sprite.Group()

# Main loop
running = True
while running:
    # Clear the Pygame window
    window.fill((150, 150, 150))

    # Draw the shapes on the frame
    _,image = cam.read()
    image = cv2.warpPerspective(image, matrix, window_size ,flags=cv2.INTER_LINEAR)
    # if len(last_pictures) > consts.PICTURES_TO_AVG: last_pictures.pop(0)
    # last_pictures.append(image)
    # avg_img = capture_and_average_images(last_pictures)
    
    # contours, hierarchy = analyzeImg(image)
    # findInImg(list(zip(contours, hierarchy[0])), curr_group)
    # big_mask.draw(window)

    mask = analyzepictures(reference_blur, image)
    # area = cv2.countNonZero(mask)
    mask = pygame.transform.flip(pygame.surfarray.make_surface(np.rot90(mask)), True, False)
    mmask = pygame.mask.from_threshold(mask, (0,0,0), threshold=(1, 1, 1))
    olist = mmask.outline()
    # print(15, len(olist))
    if len(olist) > 2: pygame.draw.polygon(window,(200,150,150),olist,0)
    

    # window.blit(mask., (0,0))
    
    # Update the Pygame display
    pygame.display.update()
    clock.tick(5)
    
    # Handle Pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

pygame.quit()
cam.release()