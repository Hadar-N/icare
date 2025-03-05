import os
import cv2
import pygame
import time
import json
import numpy as np
from logging import Logger

from utils.helper_functions.setup_helpers import asstr, followup_temp, screen_setup, sort_points
from utils.helper_functions.image_proc_helpers import create_mask, find_board, find_contours, find_threshval, get_blurred_picture, write_controured_img
import utils.consts as consts
from utils.eventBus import EventBus
from utils.dataSingleton import DataSingleton
from utils.gamePlay import GamePlay


def change_actions_decorator(method):
    def wrapper(self, *args, **kwargs):
        prev_gamestatus = self.gameplay.status

        if prev_gamestatus == consts.GAME_STATUS.ACTIVE:
            self.gameplay.pauseGame()
        
        method(self, *args, **kwargs)

        if prev_gamestatus == consts.GAME_STATUS.ACTIVE:
            self.gameplay.startGame()
    
    return wrapper

class GameEngine():
    def __init__(self, logger: Logger, eventbus: EventBus, takePicture):

        self.__running = True
        self.__counter = 0
        self.__logger = logger
        self.__eventbus = eventbus
        self.__takePicture = takePicture
        self.__matrix = self.__threshvalue = self.__reference_blur = self.__inp_coords = self.__out_coords = None
        self.__global_data = DataSingleton()
        self.__clock = pygame.time.Clock()
        
        initial_img = self.__takePicture()
    
        self.__window = self.__setup_window()
        self.__setup_comparison_data(initial_img)
        self.__eventbus.subscribe(consts.MQTT_TOPIC_CONTROL, self.__handle_control_command)
        self.gameplay = GamePlay(self.__window, self.__logger, self.__eventbus, self.__get_image_for_game)
    
    def __get_image_for_game(self, is_initial = False):
        if (self.__counter%consts.NEW_IMAGE_INTERVALS == 0 or is_initial):
            image = get_blurred_picture(self.__takePicture(), self.__matrix, self.__global_data.window_size)
            mask = create_mask(image, self.__reference_blur, self.__threshvalue)

            area = (self.__global_data.window_size[0] * self.__global_data.window_size[1]) - mask.count()
            return mask, area

    def __setup_comparison_data(self, img):
        self.__set_transformation_matrix(img)

        self.__window.fill((0, 0, 0))
        pygame.display.update()
        time.sleep(1)

        self.__set_compare_values()
        write_controured_img(img, self.__inp_coords, self.__threshvalue)
    
    def __set_transformation_matrix(self, ref = None):
        coordinates = ref if isinstance(ref, list) else None
        image = ref if isinstance(ref, np.ndarray) else None
    
        if not coordinates:
            contours = find_contours(image)
            coordinates = find_board(contours, self.__global_data.img_resize)

        ordered_points_in_board = sort_points([item[0] for item in coordinates])
        
        self.__inp_coords =  np.float32(ordered_points_in_board)
        self.__out_coords =  np.float32([[0,0], [0, self.__global_data.window_size[0] - 1], [self.__global_data.window_size[1] - 1, self.__global_data.window_size[0] - 1], [self.__global_data.window_size[1] - 1, 0]])

        self.__matrix = cv2.getPerspectiveTransform(self.__inp_coords, self.__out_coords)

        self.__logger.info(f'contouring data: inp={asstr(self.__inp_coords)}; out={asstr(self.__out_coords)}; matrix={asstr(self.__matrix)}')
    
    def __set_compare_values(self):
        new_img = self.__takePicture()
        self.__reference_blur = get_blurred_picture(new_img, self.__matrix, self.__global_data.window_size)

        self.__threshvalue = find_threshval(self.__reference_blur, consts.LIGHT_SENSITIVITY_FACTOR)
        self.__logger.info(f'threshvalue={self.__threshvalue}')

        return new_img

    def __setup_window(self):
        pygame.init()
        pygame.font.init()

        window_size, isfullscreen = screen_setup(self.__global_data.img_resize, os.getenv('PROJECTOR_RESOLUTION') if os.environ["DISPLAY"] == ":0" else None, self.__logger)
        self.__global_data.window_size = window_size
        window = pygame.display.set_mode(self.__global_data.window_size, pygame.FULLSCREEN if isfullscreen else 0)

        return window
    
    def __handle_control_command(self, message):
        message_dict = json.loads(message)
        print("handleControlCommand: ", message_dict)
        if message_dict["command"] == consts.MQTT_COMMANDS.START.value:
            self.gameplay.startGame()
            pass
        elif message_dict["command"] == consts.MQTT_COMMANDS.PAUSE.value:
            self.gameplay.pauseGame()
            pass
        elif message_dict["command"] == consts.MQTT_COMMANDS.STOP.value:
            self.gameplay.stopGame()
            pass
        elif message_dict["command"] == consts.MQTT_COMMANDS.FLIP_VIEW.value:
            self.__flip_view()
            pass
        elif message_dict["command"] == consts.MQTT_COMMANDS.RESET_DISPLAY.value:
            self.__reset_comparison_data(message_dict["payload"])
            pass
        else: print(f'invalid message/command {message_dict}')

    @change_actions_decorator
    def __reset_comparison_data(self, coordinates):
        if(not coordinates or len(coordinates) != 4):
            print('invalid coordinates!', type(coordinates), coordinates)
            return
        
        self.__set_transformation_matrix(coordinates)
        img = self.__set_compare_values()
        write_controured_img(img, self.__inp_coords, self.__threshvalue)

    @change_actions_decorator
    def __flip_view(self):
        self.__global_data.is_spin = not self.__global_data.is_spin
        self.gameplay.spinWords()

    def __event_handler(self):
        if self.__global_data.env=='pi' and followup_temp(self.__logger, self.__counter):
            pygame.display.quit()
            self.__running = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.__running = False

    def engine_loop(self):
        while self.__running:
            self.__window.fill((0,0,0))

            self.gameplay.gameLoop()

            pygame.display.update()
            self.__clock.tick(consts.CLOCK)
            self.__counter+=1

            self.__event_handler()
