import sys
import os
import numpy as np
from dotenv import load_dotenv

from utils import DataSingleton
from utils.consts import CAMERA_RES
from utils_callibration import CalibrationEngine

load_dotenv(verbose=True, override=True)
os.environ["DISPLAY"] = ":10"

global_data = DataSingleton()
global_data.env = os.getenv("ENV", 'pi')
global_data.img_resize = tuple([int(i / 2) for i in CAMERA_RES])
global_data.window_size = global_data.img_resize

def next_stage(coords):
    print("next_stage", np.array(coords).reshape(-1, 1, 2), global_data.window_size)

callibration_win = CalibrationEngine(next_stage)

if __name__ == "__main__":
    callibration_win.engine_loop()
    sys.exit()
    