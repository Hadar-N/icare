from enum import Enum

# setup consts
LOGFILE= "running.log"
CLEAN_EDGES = 25
CLOCK = 15
HIRAR_LEGEND={"NEXT":0, "PREV":1, "FIRST":2, "PARENT":3}
BOUND_LEGEND={"X":0,"Y":1,"WIDTH":2,"HEIGHT":3}
DEFAULT_WINDOW_WIDTH = 1200
IMAGE_RESIZE_WIDTH = 600

# image proc. consts
BLUR_SIZE = (21, 21)
THRESHOLD_VAL = 60 # night settings => THRESHOLD_VAL higher
THRESHOLD_MAX = 255
MIN_FRAME_CONTENT_PARTITION = 7

# text/movement consts
SPRITE_APPEAR_SPEED = 0.05
SPRITE_STUCK_THRESH = 6
SPRITE_MAX_SPEED = 5
SPRITE_MAX_OPACITY = 200
MAX_PLACEMENT_ATTAMPTS = 5
SPRITE_ANGLE_MAX_DIFF = 20
VOCAB_AMOUNT = 5
MAX_VOCAB_ACTIVE = 3
VOCAB_PATH = 'public/vocab.json'
FONT_PATH = 'public/fonts/TaipeiSansTCBeta-Regular.ttf'; FONT_SIZE= 30

# mqtt consts
MQTT_TOPIC_CONTROL = "game/control"
MQTT_TOPIC_DATA = "game/data"
class MQTT_COMMANDS(str, Enum):
    START = "start"
    PAUSE = "pause"
    STOP = "stop"