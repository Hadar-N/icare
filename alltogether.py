import cv2
import pygame
import numpy as np
import utils.consts as consts
from shapecontour import Contour, InternalSprite

cam = cv2.VideoCapture(0)
ret,image = cam.read()

if not ret:
    print("Error: Failed to capture image")

img_h, img_w, _ = image.shape
image_resize_proportion = (consts.WINDOW_WIDTH/2)/img_w
window_height = int(img_h*image_resize_proportion)

# Initialize Pygame data
pygame.init()
window_size = (consts.WINDOW_WIDTH, window_height)
clock = pygame.time.Clock()
window = pygame.display.set_mode(window_size)
curr_group = pygame.sprite.Group()

#TODO: internal animation
#TODO: check collision instead of coordinates?
#TODO: fix internal black contours

def getRandomColor() : return int(np.random.choice(range(256)))

def findInImg(img, arr, curr_group):
    # surfaces=[]
    surfaces = pygame.sprite.Group()
    count = 0
    max_elm = len(arr) - 1
    # Iterating through each contour to retrieve coordinates of each shape
    for i, zp in enumerate(reversed(arr)):
        (contour, hirar) = zp
        # if i == 0 or len(contour) < MIN_CONTOUR_POINTS or (hirar[HIRAR_LEGEND["NEXT"]] == -1 and hirar[HIRAR_LEGEND["PREV"]] == -1):
        if i == max_elm or len(contour) < consts.MIN_CONTOUR_POINTS:
            continue

        bounding = cv2.boundingRect(contour)
        prev_cont = isContourExistInGroup(curr_group, bounding)
        sim_cont = isContourExistInGroup(surfaces, bounding)

        if not sim_cont:
            surfaces.add(makeContourIntoShape(img, contour, bounding, prev_cont))
    
    curr_group.empty()
    curr_group.add(surfaces.sprites())
    surfaces.empty()

def makeContourIntoShape(img, cnt, bounding, existing):
    color_tmp = [getRandomColor(), getRandomColor(), getRandomColor()] if not existing else existing.color
    cv2.drawContours(image=img, contours=[cnt], contourIdx=-1, color=tuple(color_tmp) , thickness=cv2.FILLED)

    return Contour(img, bounding, color_tmp) if not existing else existing.updateShape(img, bounding)

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
    image = cv2.resize(image, (int(consts.WINDOW_WIDTH/2),window_height))
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) # Converting to gray image
    blurred_img = cv2.medianBlur(gray_image,consts.BLUR_CONST)
    # _, thresh_image = cv2.threshold(blurred_img, THRESHOLD_VAL, THRESHOLD_MAX, cv2.THRESH_BINARY_INV)
    thresh_image = cv2.adaptiveThreshold(blurred_img,consts.THRESHOLD_MAX,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,consts.ADAPTIVE_THRESH_AREA,consts.ADAPTIVE_THRESH_CONST)
    contours, hierarchy = cv2.findContours(thresh_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    return contours, hierarchy


# Main loop
running = True
while running:
    # Clear the Pygame window
    window.fill((150, 150, 150))

    # Draw the shapes on the frame
    _,image = cam.read()
    copy = image.copy()

    contours, hierarchy = analyzeImg(copy)
    findInImg(image.copy(), list(zip(contours, hierarchy[0])), curr_group)
    curr_group.update()
    curr_group.draw(window)

    image = np.rot90(image)
    frame_surface = pygame.surfarray.make_surface(image)
    window.blit(pygame.transform.flip(frame_surface, True, False), (consts.WINDOW_WIDTH/2, 0))

    # Update the Pygame display
    pygame.display.update()
    clock.tick(30)
    
    # Handle Pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
cam.release()