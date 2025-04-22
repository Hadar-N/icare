import os
import datetime
import logging
from dotenv import load_dotenv
import pygame

from mqtt_shared import MQTTInitialData, ConnectionManager, Topics
from game_shared import DEVICE_TYPE

from utils import DataSingleton, EventBus, GameEngine
import utils.consts as consts
from utils.helper_functions import setCameraFunctionAttempt, get_img_resize_information

load_dotenv(verbose=True, override=True)

os.environ["DISPLAY"] = f':{os.getenv("DISPLAY")}'

logging.basicConfig(filename=consts.LOGFILE)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.info(f'--------------start datetime: {datetime.datetime.now()}')

global_data = DataSingleton()
global_data.logger = logger
global_data.env = os.getenv("ENV")
global_data.is_spin = os.getenv("SPIN")
global_data.img_resize = get_img_resize_information()

takePicture, removeCamera = setCameraFunctionAttempt()

eventbus = EventBus()
gameengine = GameEngine(eventbus, takePicture)

init_data = MQTTInitialData( host = os.getenv("HOST"), port = os.getenv("PORT"), username = os.getenv("USERNAME"), password = os.getenv("PASSWORD"))
def on_message(*args, **kwargs):
    eventbus.publish(kwargs["topic"], kwargs["data"])
conn = ConnectionManager.initialize(init_data, DEVICE_TYPE.GAME, logger, on_message)

def publish_word_state(msg):
    conn.publish_message(Topics.word_state(msg["word"]["word"]), msg)
eventbus.subscribe(Topics.word_state(), publish_word_state)
eventbus.subscribe(Topics.STATE, lambda msg: conn.publish_message(Topics.STATE, msg))

gameengine.engine_loop()

logger.info("program exited")
pygame.quit()
conn.close_connection()
removeCamera()