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
from utils.setup_helpers import asstr, followup_temp, setCameraFunction, setup_window, setup_img_comparison
from utils.eventBus import EventBus
from mqtt.MQTTConnection import MQTTConnection
from utils.gamePlay import GamePlay

load_dotenv(verbose=True, override=True)

os.environ["DISPLAY"] = f':{os.getenv("DISPLAY")}'

logging.basicConfig(filename=consts.LOGFILE)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.info(f'--------------start datetime: {datetime.datetime.now()}')

global_data = DataSingleton()
global_data.env = os.getenv("ENV")
clock = pygame.time.Clock()

takePicture, removeCamera = setCameraFunction(global_data.env)

image = takePicture()

window = setup_window(logger, os.getenv('PROJECTOR_RESOLUTION') if os.environ["DISPLAY"] == ":0" else None, image)
matrix, threshvalue, reference_blur = setup_img_comparison(window, image, takePicture)

eventbus = EventBus()
gameplay = GamePlay(takePicture, window, matrix, logger, threshvalue, reference_blur, eventbus)
mqttc = MQTTConnection(logger, eventbus)

# Main loop
running = True
counter = 0

while running:
    window.fill((0,0,0))

    gameplay.gameLoop(counter)

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
mqttc.on_close()
removeCamera()