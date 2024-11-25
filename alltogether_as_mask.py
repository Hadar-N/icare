import os
import cv2
import pygame
import numpy as np
import datetime
import time
import logging
from picamera2 import Picamera2

import utils.consts as consts
from utils.dataSingleton import DataSingleton
from utils.setup_helpers import asstr, screenSetup, getTransformationMatrix, originImageResize, get_pi_temp
from utils.internals_management_helpers import AddSpritesToGroup, checkCollision, getFishOptions

os.environ["DISPLAY"] = ":0"

logging.basicConfig(filename=consts.LOGFILE)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.info(f'--------------start datetime: {datetime.datetime.now()}')

camera = Picamera2()

config = camera.create_preview_configuration(
    main={"size": (1640, 1232), "format": "BGR888"},
    buffer_count=2
)

camera.configure(config)
camera.start()
image = camera.capture_array()

global_data = DataSingleton()
pygame.init()
clock = pygame.time.Clock()

img_resize = originImageResize(image)
window_size, window_flags = screenSetup(img_resize, logger)
global_data.window_size = window_size
window = pygame.display.set_mode(global_data.window_size, window_flags)

internals = pygame.sprite.Group()
kernel = np.ones((11, 11), np.uint8)  # Larger kernel for more aggressive closing

def findContours(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, consts.THRESHOLD_VAL, consts.THRESHOLD_MAX, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def createMask(current_image):
    current_blurred = cv2.GaussianBlur(current_image, consts.BLUR_SIZE, 0)
    difference = cv2.absdiff(current_blurred, reference_blur)
    gray_image = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray_image, consts.THRESHOLD_VAL, consts.THRESHOLD_MAX, cv2.THRESH_BINARY_INV)
    closed = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, kernel)

    return closed

image = cv2.resize(image, img_resize)
contours = findContours(image)
inp, out, matrix = getTransformationMatrix(contours, img_resize, global_data.window_size)

window.fill((0, 0, 0))
pygame.display.update()
time.sleep(2)  # Wait for 2 seconds
# get darkened reference image
reference_image = cv2.flip(cv2.warpPerspective(cv2.resize(camera.capture_array(), img_resize), matrix, (global_data.window_size[1], global_data.window_size[0]) ,flags=cv2.INTER_LINEAR), 0)
reference_blur = cv2.GaussianBlur(reference_image, consts.BLUR_SIZE, 0)

fish_options = getFishOptions()
global_data.fish_options = fish_options
internals = pygame.sprite.Group()

def renewCameraPicture(counter, mask, area, mask_img, image):
    if (counter%(consts.CLOCK/2) == 0 or not mask or not area):
        image = cv2.resize(camera.capture_array(), img_resize)
        image = cv2.flip(cv2.warpPerspective(image, matrix,  (global_data.window_size[1], global_data.window_size[0]) ,flags=cv2.INTER_LINEAR), 0)

        mask_img = createMask(image)
        mask_img = cv2.bitwise_not(mask_img)

        mask_img_rgb = pygame.surfarray.make_surface(cv2.cvtColor(mask_img, cv2.COLOR_GRAY2RGB))
        mask = pygame.mask.from_threshold(mask_img_rgb, (0,0,0), threshold=(1,1,1))
        area = (global_data.window_size[0] * global_data.window_size[1]) - mask.count()

    return mask,area,mask_img, image

# Main loop
running = True
counter = 0
mask = area = mask_img = image = None

while running:
    window.fill((0,0,0))

    mask, area, mask_img, image = renewCameraPicture(counter, mask, area, mask_img, image)

    AddSpritesToGroup(internals, mask, area)
    checkCollision(internals, mask)

    internals.update()
    internals.draw(window)

    pygame.display.update()
    clock.tick(consts.CLOCK)
    counter+=1

    if (counter%100 == 0):
        temp = get_pi_temp()
        if (temp < 65):
            logger.info(f'temp: {temp}')
        elif (temp < 77):
            logger.warning(f'temp: {temp}')
        else:
            logger.critical(f'temp: {temp} ==> program exited')
            pygame.display.quit()
            running = False
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

pygame.quit()
cv2.destroyAllWindows()
camera.stop()