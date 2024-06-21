import cv2
import pygame
import numpy as np
from PIL import Image

BLUR_CONST = 3
ADAPTIVE_THRESH_AREA = 11; ADAPTIVE_THRESH_CONST = 2; COMPARISON_VALUE = 7
THRESHOLD_VAL = 220; THRESHOLD_MAX = 255
MIN_CONTOUR_POINTS = 100; CONTOUR_WEIGHT = 1
EPSILON = 0.01
HIRAR_LEGEND={"NEXT":0, "PREV":1, "FIRST":2, "PARENT":3}
BOUND_LEGEND={"X":0,"Y":1,"WIDTH":2,"HEIGHT":3}
# IMAGE_PATH = 'image.png'
# IMAGE_PATH = 'm_2_inverted.png'
IMAGE_PATH = 'm_3.png'
WINDOW_WIDTH = 800

# Load image using OpenCV
image = cv2.imread(IMAGE_PATH)
# image = Image.fromarray(np.flipud(image))
# image= np.rot90(image)
img_h, img_w, _ = image.shape
image_resize_proportion = (WINDOW_WIDTH/2)/img_w
window_height = int(img_h*image_resize_proportion)
image = cv2.resize(image, (int(WINDOW_WIDTH/2),window_height))

# Initialize Pygame data
pygame.init()
window_size = (WINDOW_WIDTH, window_height)
clock = pygame.time.Clock()
window = pygame.display.set_mode(window_size)

gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) # Converting to gray image
blurred_img = cv2.medianBlur(gray_image,BLUR_CONST)
# _, thresh_image = cv2.threshold(blurred_img, THRESHOLD_VAL, THRESHOLD_MAX, cv2.THRESH_BINARY_INV)
thresh_image = cv2.adaptiveThreshold(blurred_img,THRESHOLD_MAX,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,ADAPTIVE_THRESH_AREA,ADAPTIVE_THRESH_CONST)
contours, hierarchy = cv2.findContours(thresh_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

def getRandomColor() : return int(np.random.choice(range(256)))

def findInImg(img, arr):
    surfaces=[]
    count = 0
    max_elm = len(arr) - 1
    # Iterating through each contour to retrieve coordinates of each shape
    for i, zp in enumerate(reversed(arr)):
        (contour, hirar) = zp
        # if i == 0 or len(contour) < MIN_CONTOUR_POINTS or (hirar[HIRAR_LEGEND["NEXT"]] == -1 and hirar[HIRAR_LEGEND["PREV"]] == -1):
        if i == max_elm or len(contour) < MIN_CONTOUR_POINTS:
            continue

        # TODO: check what's smaller then override
        bounding = cv2.boundingRect(contour)
        if isShouldAddContour(surfaces, bounding):
            count+=1
            surfaces.append(makeContourIntoShape(img, contour, bounding, i))
        # cv2.drawContours(image=img, contours=[contour], contourIdx=-1, color=tuple(COLOR) , thickness=cv2.FILLED)
    return surfaces

def makeContourIntoShape(img, cnt, bounding, index):
    color_tmp = [getRandomColor(), getRandomColor(), getRandomColor()]
    cv2.drawContours(image=img, contours=[cnt], contourIdx=-1, color=tuple(color_tmp) , thickness=cv2.FILLED)

    frame_surface = (pygame.transform.flip(pygame.surfarray.make_surface(np.rot90(img)), True, False)).subsurface(bounding)
    frame_mask = pygame.mask.from_threshold(frame_surface, color_tmp, threshold=(1, 1, 1))
    final_subsurface = frame_mask.to_surface()
    final_subsurface.set_colorkey((0,0,0))

    # TODO: fix internal black contours

    # color the contours
    for x in range(int(bounding[2])):
        for y in range(int(bounding[3])):
            if final_subsurface.get_at((x,y))[0] != 0:
                final_subsurface.set_at((x,y),color_tmp)

    return {"x":bounding[BOUND_LEGEND["X"]], "y":bounding[BOUND_LEGEND["Y"]], "s": final_subsurface, "height":bounding[BOUND_LEGEND["HEIGHT"]] , "width": bounding[BOUND_LEGEND["WIDTH"]]}

def isShouldAddContour(s_list, c_bound):
    if (any(isSameContours(item, c_bound) for item in s_list)):
        return False
    
    return True

def isSameContours(s_item, c_bound):
    location_same = abs(s_item["x"] - c_bound[BOUND_LEGEND["X"]]) < COMPARISON_VALUE and abs(s_item["y"] - c_bound[BOUND_LEGEND["Y"]]) < COMPARISON_VALUE
    size_same = abs(s_item["height"] - c_bound[BOUND_LEGEND["HEIGHT"]]) < COMPARISON_VALUE*2 and abs(s_item["width"] - c_bound[BOUND_LEGEND["WIDTH"]]) < COMPARISON_VALUE*2
    return location_same and size_same

# Main loop
running = True
while running:
    # Clear the Pygame window
    window.fill((150, 150, 150))

    # Draw the shapes on the frame
    copy = image.copy()
    surfaces = findInImg(image.copy(), list(zip(contours, hierarchy[0])))
    for s in surfaces:
        window.blit(s["s"], (s["x"], s["y"]))

    copy = np.rot90(copy)
    frame_surface = pygame.surfarray.make_surface(copy)
    # frame_mask = pygame.mask.from_threshold(frame_surface, COLOR, threshold=(1, 1, 1))
    # new_surf = frame_mask.to_surface()
    # new_surf.set_colorkey((0,0,0))
    # flipped = pygame.transform.flip(new_surf, True, False)

    # window.blit(flipped, (0, 0))
    window.blit(pygame.transform.flip(frame_surface, True, False), (WINDOW_WIDTH/2, 0))

    # for point in frame_mask.outline():
    #     x = point[0]
    #     y = point[1]
    #     pygame.draw.circle(window,'red',(x,y),1)

    # Update the Pygame display
    pygame.display.update()
    clock.tick(1)
    
    # Handle Pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
