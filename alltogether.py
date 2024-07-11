import cv2
import pygame
import numpy as np
import utils.consts as consts
from shapecontour import ContourPolygon
from utils.helpers import screenSetup, getTransformationMatrix

# image = cv2.imread(consts.IMAGE_PATH)
cam = cv2.VideoCapture(0)
ret,image = cam.read()

if not ret:
    print("Error: Failed to capture image")

# Initialize Pygame data
pygame.init()
clock = pygame.time.Clock()

window_size, img_resize, output_resize_proportion, window_flags = screenSetup(image)
print(window_size, img_resize, output_resize_proportion, window_flags)
window = pygame.display.set_mode(window_size, window_flags)

curr_group = pygame.sprite.Group()
    
#TODO: Problem: photo proportion vs projector proportion => shift in image
#TODO: inner shapes only (on board)
#TODO: fix internal black contours
#TODO: change inner sprite location/remove it and add new if changes effect it

def findInImg(arr, curr_group):
    surfaces = pygame.sprite.Group()
    max_elm = len(arr) - 1
    # Iterating through each contour to retrieve coordinates of each shape
    for i, zp in enumerate(reversed(arr)):
        (contour, hirar) = zp
        # print(f"contour no. {i}'s hirar: ", hirar, " & bounding: ", cv2.boundingRect(contour))
        cnt_area = cv2.contourArea(contour)
        # if i == 0 or len(contour) < MIN_CONTOUR_POINTS or (hirar[HIRAR_LEGEND["NEXT"]] == -1 and hirar[HIRAR_LEGEND["PREV"]] == -1):
        if i == max_elm or cnt_area < consts.MIN_CONTOUR_POINTS:
            continue

        temp_sprite = ContourPolygon(contour, output_resize_proportion)
        prev_spr = isSpriteExistInGroup(curr_group, temp_sprite)
        sim_spr = isSpriteExistInGroup(surfaces, temp_sprite)

        # print("prev_spr: ", prev_spr, "sim_spr: ",  sim_spr)

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
    thresh_image = cv2.adaptiveThreshold(dialated,consts.THRESHOLD_MAX,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,consts.ADAPTIVE_THRESH_AREA,consts.ADAPTIVE_THRESH_CONST)
    contours, hierarchy = cv2.findContours(thresh_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    return contours, hierarchy


image = cv2.resize(image, img_resize)
contours, _ = analyzeImg(image)
inp, new, matrix = getTransformationMatrix(contours, img_resize, window_size)
print(inp, new, matrix)
# findInImg(list(zip(contours, hierarchy[0])), curr_group)
# curr_group.update()
# curr_group.draw(window)

# cv2.drawContours(image, inp, -1, (255,0,0), 3)
# cv2.drawContours(image, new, -1, (0,255,0), 3)
# Main loop
running = True
while running:
    # Clear the Pygame window
    window.fill((150, 150, 150))

    # Draw the shapes on the frame
    _,image = cam.read()
    image = cv2.warpPerspective(cv2.resize(image, img_resize) , matrix, img_resize ,flags=cv2.INTER_LINEAR)
    
    contours, hierarchy = analyzeImg(image)

    findInImg(list(zip(contours, hierarchy[0])), curr_group)
    curr_group.update()
    curr_group.draw(window)

    # copy = np.rot90(image)
    # frame_surface = pygame.surfarray.make_surface(copy)
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