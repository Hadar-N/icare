import os
import pygame
import datetime
import logging
from dotenv import load_dotenv

from mqtt_shared import MQTTInitialData, ConnectionManager, Topics
from game_shared import DEVICE_TYPE

from utils import DataSingleton, EventBus, GameEngine
import utils.consts as consts
from utils.helper_functions import setCameraFunction, get_img_resize_information

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

init_data = MQTTInitialData(
    host = os.getenv("HOST"),
    port = os.getenv("PORT"),
    username = os.getenv("USERNAME"),
    password = os.getenv("PASSWORD")
)

def on_message(*args, **kwargs):
    eventbus.publish(kwargs["topic"], kwargs["data"])
def publish_message(msg):
    conn.publish_message(Topics.DATA, msg)

conn = ConnectionManager.initialize(init_data, DEVICE_TYPE.GAME, logger, on_message)
eventbus.subscribe(Topics.DATA, publish_message, True)

gameengine.engine_loop()

logger.info("program exited")
pygame.quit()
conn.close_connection()
removeCamera()