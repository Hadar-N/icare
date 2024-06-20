import cv2
import pygame
import numpy as np

BLUR_CONST = 5
ADAPTIVE_THRESH_AREA = 21; ADAPTIVE_THRESH_CONST = 2
THRESHOLD_VAL = 220; THRESHOLD_MAX = 255
MIN_CONTOUR_POINTS = 100; CONTOUR_WEIGHT = 5; CONTOUR_COLOR = (255, 0, 0)
EPSILON = 0.01
HIRAR_LEGEND={"NEXT":0, "PREV":1, "FIRST":2, "PARENT":3}
IMAGE_PATH = 'image.png'  # Replace with your image path
WINDOW_WIDTH = 800

# Load image using OpenCV
image = cv2.imread(IMAGE_PATH)
img_h, img_w, _ = image.shape
window_height = int(img_h*((WINDOW_WIDTH/2)/img_w))
image = cv2.resize(image, (int(WINDOW_WIDTH/2),window_height))

# Initialize Pygame data
pygame.init()
window_size = (WINDOW_WIDTH, window_height)
clock = pygame.time.Clock()
window = pygame.display.set_mode(window_size)

gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) # Converting to gray image
blurred_img = cv2.medianBlur(gray_image,BLUR_CONST)
thresh_image = cv2.adaptiveThreshold(blurred_img,THRESHOLD_MAX,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,ADAPTIVE_THRESH_AREA,ADAPTIVE_THRESH_CONST)
contours, hierarchy = cv2.findContours(thresh_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

def getRandomColor() : return int(np.random.choice(range(256)))

COLOR = [getRandomColor()] * 3

def findInImg(img, arr):
    surfaces=[]
    count = 0
    # Iterating through each contour to retrieve coordinates of each shape
    for i, zp in enumerate(arr):
        (contour, hirar) = zp
        if i == 0 or len(contour) < MIN_CONTOUR_POINTS or (hirar[HIRAR_LEGEND["NEXT"]] == -1 and hirar[HIRAR_LEGEND["PREV"]] == -1):
            continue

        count+=1
        cv2.drawContours(image=img, contours=[contour], contourIdx=-1, color=tuple(COLOR) , thickness=cv2.FILLED)
        surfaces.append(contour)
    return img


# Main loop
running = True
while running:
    # Clear the Pygame window
    window.fill((150, 150, 150))

    # Draw the shapes on the frame
    copy = findInImg(image.copy(), zip(contours, hierarchy[0]))

    copy = np.rot90(copy)
    frame_surface = pygame.surfarray.make_surface(copy)
    frame_mask = pygame.mask.from_threshold(frame_surface, COLOR, threshold=(1, 1, 1))
    new_surf = frame_mask.to_surface()
    new_surf.set_colorkey((0,0,0))

    frame_mask.outline()
    window.blit(pygame.transform.flip(new_surf, True, False), (0, 0))
    window.blit(pygame.transform.flip(frame_surface, True, False), (WINDOW_WIDTH/2, 0))
    
    # Update the Pygame display
    pygame.display.update()
    clock.tick(1)
    
    # Handle Pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
