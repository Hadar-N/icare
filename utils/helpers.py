import numpy as np
from screeninfo import get_monitors
from utils.consts import IMAGE_RESIZE_WIDTH, WINDOW_WIDTH
import os

def getRandomColor() : return int(np.random.choice(range(256)))

def get_secondary_monitor():
    monitors = get_monitors()
    if len(monitors) > 1:
        return monitors[1]  # Return the second monitor
    return None


def screenSetup(img):
    img_h, img_w, _ = img.shape
    img_w_resized = IMAGE_RESIZE_WIDTH
    img_resized_proportion = img_w_resized/img_w
    img_h_resized = int(img_h * img_resized_proportion)

    window_width = WINDOW_WIDTH
    output_resize_proportion = window_width/img_w_resized
    window_height = img_h_resized*output_resize_proportion
    screen_x = 0
    screen_y = 0

    secondary_monitor = get_secondary_monitor()
    if secondary_monitor:
        window_height = secondary_monitor.height
        output_resize_proportion = window_height/img_h_resized
        window_width = int(img_w_resized*output_resize_proportion)
        screen_x = secondary_monitor.x
        screen_y = secondary_monitor.y

        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{screen_x},{screen_y}"
    else:
        print("Secondary monitor not found")

    window_size = (int(window_width), window_height)
    img_resize = (img_w_resized, int(img_h_resized))

    return (window_size, img_resize, output_resize_proportion)


