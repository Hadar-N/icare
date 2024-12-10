import os
import cv2
import pygame
import numpy as np
import datetime
import time
import logging
from dotenv import load_dotenv

import utils.consts as consts
from utils.dataSingleton import DataSingleton
from utils.setup_helpers import asstr, screenSetup, getTransformationMatrix, originImageResize, followup_temp, findContours, setCameraFunction
from utils.internals_management_helpers import AddSpritesToGroup, checkCollision, getFishOptions
from utils.vocab_management_helpers import initVocabOptions, AddVocabToGroup, vocabReadMaskCollision, presentNewZHVocab, vocabMatching

load_dotenv(verbose=True, override=True)

os.environ["DISPLAY"] = f':{os.getenv("DISPLAY")}'

def renewCameraPicture(counter, mask, area, mask_img, image):
    if (counter%(consts.CLOCK/2) == 0 or not mask or not area):
        image = cv2.resize(takePicture(), img_resize)
        image = cv2.flip(cv2.warpPerspective(image, matrix,  (global_data.window_size[1], global_data.window_size[0]) ,flags=cv2.INTER_LINEAR), 0)

        mask_img = createMask(image)
        mask_img = cv2.bitwise_not(mask_img)

        mask_img_rgb = pygame.surfarray.make_surface(cv2.cvtColor(mask_img, cv2.COLOR_GRAY2RGB))
        mask = pygame.mask.from_threshold(mask_img_rgb, (0,0,0), threshold=(1,1,1))
        area = (global_data.window_size[0] * global_data.window_size[1]) - mask.count()

    return mask,area,mask_img, image

def createMask(current_image):
    current_blurred = cv2.GaussianBlur(current_image, consts.BLUR_SIZE, 0)
    difference = cv2.absdiff(current_blurred, reference_blur)
    gray_image = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray_image, threshvalue, consts.THRESHOLD_MAX, cv2.THRESH_BINARY_INV)
    closed = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, kernel)
    return closed

def findthreshval(empty_image):
    val = np.mean(np.mean(empty_image, axis=(0,1)), axis=0)
    return val

logging.basicConfig(filename=consts.LOGFILE)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.info(f'--------------start datetime: {datetime.datetime.now()}')

global_data = DataSingleton()
global_data.env = os.getenv("ENV")
pygame.init()
clock = pygame.time.Clock()
pygame.font.init()

takePicture, removeCamera = setCameraFunction(global_data.env)
image = takePicture()

img_resize = originImageResize(image)
window_size, window_flags = screenSetup(img_resize, os.getenv('PROJECTOR_RESOLUTION'), logger)
global_data.window_size = window_size
window = pygame.display.set_mode(global_data.window_size, window_flags)

image = cv2.resize(image, img_resize)
contours = findContours(image)
inp, out, matrix = getTransformationMatrix(contours, img_resize, global_data.window_size)

window.fill((0, 0, 0))
pygame.display.update()
time.sleep(2)  # Wait for 2 seconds
# get darkened reference image
kernel = np.ones((11, 11), np.uint8)  # Larger kernel for more aggressive closing
reference_image = cv2.flip(cv2.warpPerspective(cv2.resize(takePicture(), img_resize), matrix, (global_data.window_size[1], global_data.window_size[0]) ,flags=cv2.INTER_LINEAR), 0)
reference_blur = cv2.GaussianBlur(reference_image, consts.BLUR_SIZE, 0)
threshvalue = findthreshval(reference_blur) * 1.2
print("threshvalue: ", findthreshval(reference_blur), threshvalue)

initVocabOptions()
vocabengroup = pygame.sprite.Group()
vocabzhbankgroup = pygame.sprite.Group()
vocabzhdrawgroup = pygame.sprite.Group()
AddVocabToGroup(vocabengroup, vocabzhbankgroup)

# Main loop
running = True
counter = 0
mask = area = mask_img = image = None

while running:
    window.fill((0,0,0))

    mask, area, mask_img, image = renewCameraPicture(counter, mask, area, mask_img, image)

    vocabMatching(logger, vocabengroup, vocabzhdrawgroup)
    
    presentNewZHVocab(vocabzhbankgroup, vocabzhdrawgroup, mask, area)
    checkCollision(vocabzhdrawgroup, mask, global_data.window_size)
    vocabReadMaskCollision(vocabengroup, mask)

    vocabzhdrawgroup.update()
    vocabzhdrawgroup.draw(window)
    vocabengroup.draw(window)

    pygame.display.update()
    clock.tick(consts.CLOCK)
    counter+=1

    if global_data.env=='pi' and followup_temp(logger, counter):
        pygame.display.quit()
        running = False
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

pygame.quit()
removeCamera()