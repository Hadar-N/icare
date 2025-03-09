from enum import Enum
import numpy as np

# setup consts
LOGFILE= "running.log"
CLEAN_EDGES = 25
CLOCK = 16
NEW_IMAGE_INTERVALS = CLOCK/2
HIRAR_LEGEND={"NEXT":0, "PREV":1, "FIRST":2, "PARENT":3}
BOUND_LEGEND={"X":0,"Y":1,"WIDTH":2,"HEIGHT":3}
DEFAULT_WINDOW_WIDTH = 1200
IMAGE_RESIZE_WIDTH = 600
CAMERA_RES = (1640, 1232)
CONTOUR_IMAGE_LOC="tests/image_with_contours.jpg"

# game constants
VOCAB_AMOUNT = 5
MAX_VOCAB_ACTIVE = 3
class GAME_STATUS(str, Enum):
    ACTIVE= "active"
    HALTED= "halted"
    DONE= "done"

# image proc. consts
BLUR_SIZE = (21, 21)
THRESHOLD_MAX = 255
MIN_FRAME_CONTENT_PARTITION = 7
KERNEL = np.ones((11, 11), np.uint8)
LIGHT_SENSITIVITY_FACTOR = 1.4 # TODO: calc based on lighting conditions???

# text/movement consts
SPRITE_APPEAR_SPEED = 0.05
SPRITE_STUCK_THRESH = 6
SPRITE_MAX_SPEED = 5
SPRITE_MIN_SPEED = 1
SPRITE_MAX_OPACITY = 200
MAX_PLACEMENT_ATTAMPTS = 5
SPRITE_ANGLE_MAX_DIFF = 20
VOCAB_PATH = 'public/vocab.json'
FONT_PATH = 'public/fonts/TaipeiSansTCBeta-Regular.ttf'; FONT_SIZE= 30

# mqtt consts
MQTT_TOPIC_CONTROL = "game/control"
MQTT_TOPIC_DATA = "game/data"
class MQTT_DATA_ACTIONS(str,Enum):
    NEW = "new"
    REMOVE = "remove"
    MATCHED = "matched"
    STATUS = "status"
class MQTT_COMMANDS(str, Enum):
    START = "start"
    PAUSE = "pause"
    STOP = "stop"
    RESET_DISPLAY = "reset_display"
    FLIP_VIEW = "flip_view"