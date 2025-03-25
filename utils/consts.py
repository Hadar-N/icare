from enum import Enum
import numpy as np

from game_shared import GAME_MODES

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
MAX_VOCAB_ACTIVE = 1

# image proc. consts
BLUR_SIZE = (21, 21)
THRESHOLD_MAX = 255
MIN_FRAME_CONTENT_PARTITION = 10
KERNEL = np.ones((11, 11), np.uint8)
BORDER_SIZE = 50
class HIRAR_LOCATIONS (Enum):
    NEXT = 0
    PREV = 1
    CHILD = 2
    PARENT = 3

# text/movement consts
SPRITE_APPEAR_SPEED = 0.05
SPRITE_STUCK_THRESH = 6
SPRITE_MAX_SPEED = 5
SPRITE_MIN_SPEED = 1
SPRITE_MAX_OPACITY = 200
MAX_PLACEMENT_ATTAMPTS = 5
SPRITE_ANGLE_MAX_DIFF = 20
MIN_DISTANCE_TO_TWIN = 4 #times the twin size
VOCAB_PATH = {
    GAME_MODES.ENtoZH: 'public/english_to_chinese.json',
    GAME_MODES.ZHtoEN: 'public/chinese_to_english.json'
}
FONT_PATH = 'public/fonts/DFT_K90.ttf'
FONT_SIZE= 30