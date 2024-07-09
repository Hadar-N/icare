import cv2
import pygame
import numpy as np
import utils.consts as consts
from shapecontour import ContourPolygon
from utils.helpers import screenSetup

cam = cv2.VideoCapture(0)
ret,image = cam.read()

if not ret:
    print("Error: Failed to capture image")

# Initialize Pygame data
pygame.init()
clock = pygame.time.Clock()

window_size, img_resize, output_resize_proportion = screenSetup(image)
window = pygame.display.set_mode(window_size,pygame.FULLSCREEN)

curr_group = pygame.sprite.Group()

#TODO: fix internal black contours
#TODO: change inner sprite location/remove it and add new if changes effect it

def getRandomColor() : return int(np.random.choice(range(256)))

def findInImg(arr, curr_group):
    surfaces = pygame.sprite.Group()
    max_elm = len(arr) - 1
    # Iterating through each contour to retrieve coordinates of each shape
    for i, zp in enumerate(reversed(arr)):
        (contour, hirar) = zp
        cnt_area = cv2.contourArea(contour)
        # if i == 0 or len(contour) < MIN_CONTOUR_POINTS or (hirar[HIRAR_LEGEND["NEXT"]] == -1 and hirar[HIRAR_LEGEND["PREV"]] == -1):
        if i == max_elm or cnt_area < consts.MIN_CONTOUR_POINTS:
            continue

        temp_sprite = ContourPolygon(contour, output_resize_proportion)
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
    kernel = np.ones((5, 5), np.uint8)
    dialated = cv2.dilate(blurred_img, kernel, iterations=1)
    thresh_image = cv2.adaptiveThreshold(dialated,consts.THRESHOLD_MAX,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,consts.ADAPTIVE_THRESH_AREA,consts.ADAPTIVE_THRESH_CONST)
    contours, hierarchy = cv2.findContours(thresh_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    return contours, hierarchy

def findBoard(conts):
    rects = []
    i=0
    for contour in conts:
        cnt_area = cv2.contourArea(contour)
        if i == 0 or cnt_area > consts.MIN_CONTOUR_POINTS:
            i+=1
            epsilon = 0.05 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            if len(approx) == 4:
                # cv2.drawContours(image, contour, -1, (0,0,255), 3)
                rects.append((cnt_area, approx, contour))

    if len(rects) == 0:
        #TODO: write actual conts[0] boundaries
        return (cv2.contourArea(conts[0]), conts[0], conts[0])
    if len(rects) == 1: return rects[0]
    else:
        #TODO: choose the most logical option instead of the biggest one
        return max(rects, key=lambda r: r[0])

# image = cv2.resize(image, (window_width,window_height))
# contours, hierarchy = analyzeImg(image)
# cnt_area, cnt_approx, cnt_contour = findBoard(contours)
# cv2.drawContours(image, cnt_contour, -1, (255,0,0), 3)

#TODO: transform perspective
#TODO: inner shapes only (on board)
#TODO: check shift to the side

# Main loop
running = True
while running:
    # Clear the Pygame window
    window.fill((150, 150, 150))

    # Draw the shapes on the frame
    _,image = cam.read()
    image = cv2.resize(image, img_resize)
    
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