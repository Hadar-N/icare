import cv2
import pygame
import numpy as np
import utils.consts as consts
from shapecontour import ContourPolygon
# import tkinter

cam = cv2.VideoCapture(0)
ret,image = cam.read()
# image = cv2.imread(consts.IMAGE_PATH)

# root = tkinter.Tk()
# WIN_WIDTH = root.winfo_screenwidth() - 50
# WIN_HEIGHT = root.winfo_screenheight() - 50

if not ret:
    print("Error: Failed to capture image")

img_h, img_w, _ = image.shape
image_resize_proportion = (consts.WINDOW_WIDTH/2)/img_w
window_height = int(img_h*image_resize_proportion)
# window_height = WIN_HEIGHT

# Initialize Pygame data
pygame.init()
window_size = (int(consts.WINDOW_WIDTH/2), window_height)
clock = pygame.time.Clock()
window = pygame.display.set_mode(window_size, pygame.RESIZABLE)
curr_group = pygame.sprite.Group()

#TODO: fix internal black contours
#TODO: change sprite location/remove it and add new if changes effect it
#TODO: ?? check collision instead of coordinates when comparing contours (old/new)

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

        bounding = cv2.boundingRect(contour)

        prev_cont = isContourExistInGroup(curr_group, bounding, cnt_area)
        sim_cont = isContourExistInGroup(surfaces, bounding, cnt_area)

        if not sim_cont:
            surfaces.add(ContourPolygon(contour, bounding) if not prev_cont else prev_cont.updateShape(contour, bounding))
    
    curr_group.empty()
    curr_group.add(surfaces.sprites())
    surfaces.empty()

def isContourExistInGroup(s_group, contour, c_area):
    relevant = next((item for item in s_group.sprites() if isSameContours(item, contour, c_area)), None)
    if (relevant):
        return relevant
    
    return False

# def isSameContours(s_item, c_bound, c_area):
#     cnt_area
#     # location_same = abs(s_item.rect.x - c_bound[consts.BOUND_LEGEND["X"]]) < consts.COMPARISON_VALUE and abs(s_item.rect.y - c_bound[consts.BOUND_LEGEND["Y"]]) < consts.COMPARISON_VALUE
#     # size_same = abs(s_item.rect.height - c_bound[consts.BOUND_LEGEND["HEIGHT"]]) < consts.COMPARISON_VALUE*2 and abs(s_item.rect.width - c_bound[consts.BOUND_LEGEND["WIDTH"]]) < consts.COMPARISON_VALUE*2
#     return location_same and size_same


def isSameContours(s_item, cnt, c_area):
    # for sprite in sprite_group:
        polygon_contour = s_item.dots
        print(polygon_contour)
        
        # Convert to numpy array format compatible with OpenCV
        # polygon_contour = np.array(polygon_points).reshape((-1, 1, 2)).astype(np.int32)
        polygon_area = cv2.contourArea(polygon_contour)
        print(polygon_area)

        print(cv2.isContourConvex(cv2.convexHull(polygon_contour)))
        print(cv2.isContourConvex(cv2.convexHull(cnt)))

        # Calculate intersection area
        intersection = cv2.intersectConvexConvex(cnt, polygon_contour)
        intersection_area = cv2.contourArea(intersection)
                
        # Check if the areas are similar
        if intersection_area / c_area > consts.SAME_CONTOUR_THRESHOLD and intersection_area / polygon_area > consts.SAME_CONTOUR_THRESHOLD:
            return s_item
    
    # return None


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

# Main loop
running = True
while running:
    # Clear the Pygame window
    window.fill((150, 150, 150))

    # Draw the shapes on the frame
    _,image = cam.read()
    image = cv2.resize(image, (int(consts.WINDOW_WIDTH/2),window_height))
    
    copy = image.copy()

    contours, hierarchy = analyzeImg(image)
    findInImg(copy, list(zip(contours, hierarchy[0])), curr_group)
    curr_group.update()
    curr_group.draw(window)

    # image = np.rot90(image)
    # frame_surface = pygame.surfarray.make_surface(image)
    # window.blit(pygame.transform.flip(frame_surface, True, False), (consts.WINDOW_WIDTH/2, 0))

    # Update the Pygame display
    pygame.display.update()
    clock.tick(30)
    
    # Handle Pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

pygame.quit()
cam.release()