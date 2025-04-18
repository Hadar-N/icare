import sys
import os
import json
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
    command_name = 'python' if global_data.env == "pi" else 'py'
    params = json.dumps({'"coords"': np.array(coords).reshape(-1, 1, 2).tolist(), '"win_size"':global_data.window_size})
    os.execvp(command_name, [command_name, "main.py", params])

callibration_win = CalibrationEngine(next_stage)

if __name__ == "__main__":
    callibration_win.engine_loop()
    sys.exit()
    