import os
import pygame
import datetime
import logging
from dotenv import load_dotenv

import utils.consts as consts
from utils.dataSingleton import DataSingleton
from utils.helper_functions.setup_helpers import setCameraFunction, get_img_resize_information
from utils.eventBus import EventBus
from mqtt.MQTTConnection import MQTTConnection
from utils.gameEngine import GameEngine

load_dotenv(verbose=True, override=True)

os.environ["DISPLAY"] = f':{os.getenv("DISPLAY")}'

logging.basicConfig(filename=consts.LOGFILE)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.info(f'--------------start datetime: {datetime.datetime.now()}')

global_data = DataSingleton()
global_data.env = os.getenv("ENV")
global_data.is_spin = os.getenv("SPIN")
global_data.img_resize = get_img_resize_information()

takePicture, removeCamera = setCameraFunction(global_data.env, global_data.img_resize)

eventbus = EventBus()
gameengine = GameEngine(logger, eventbus, takePicture)
mqttc = MQTTConnection(logger, eventbus)

gameengine.engine_loop()

logger.info("program exited")
pygame.quit()
mqttc.on_close()
removeCamera()