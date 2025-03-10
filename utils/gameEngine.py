import os
import cv2
import pygame
import time
import json
import numpy as np
from logging import Logger

from utils.helper_functions.setup_helpers import asstr, followup_temp, screen_setup
from utils.helper_functions.image_proc_helpers import create_mask, set_transformation_matrix, set_compare_values, get_blurred_picture, write_controured_img, get_transformation_matrix_with_borders
import utils.consts as consts
from utils.eventBus import EventBus
from utils.dataSingleton import DataSingleton
from utils.gamePlay import GamePlay


def change_actions_decorator(method):
    def wrapper(self, *args, **kwargs):
        prev_gamestatus = self.gameplay.status

        if prev_gamestatus == consts.GAME_STATUS.ACTIVE:
            self.gameplay.pause_game()
        
        method(self, *args, **kwargs)

        if prev_gamestatus == consts.GAME_STATUS.ACTIVE:
            self.gameplay.start_game()
    
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
        self.__eventbus.subscribe(consts.MQTT_TOPIC_DATA, self.__add_time_to_payload)
        self.gameplay = GamePlay(self.__window, self.__logger, self.__eventbus, self.__get_image_for_game)
    
    def __add_time_to_payload(self, payload):
        for x in payload:
            x["time"]=self.__counter / consts.CLOCK

    def __get_image_for_game(self, is_initial = False):
        if (self.__counter%consts.NEW_IMAGE_INTERVALS == 0 or is_initial):
            image = get_blurred_picture(self.__takePicture(), self.__matrix, self.__global_data.window_size)
            mask = create_mask(image, self.__reference_blur, self.__threshvalue)

            area = (self.__global_data.window_size[0] * self.__global_data.window_size[1]) - mask.count()
            return mask, area
        return None

    def __setup_comparison_data(self, img):
        self.__inp_coords, self.__out_coords, self.__matrix = set_transformation_matrix(self.__global_data, img)
        bordered_matrix, inp_coords_bordered = get_transformation_matrix_with_borders(self.__inp_coords, self.__out_coords, self.__global_data.img_resize)
        self.__logger.info(f'automatic contouring data: inp={asstr(self.__inp_coords)}; out={asstr(self.__out_coords)}; matrix={asstr(self.__matrix)}')

        self.__window.fill((0, 0, 0))
        pygame.display.update()
        time.sleep(1)

        self.__reference_blur, self.__threshvalue, _ = set_compare_values(self.__takePicture, self.__matrix, bordered_matrix, self.__global_data.window_size, self.__logger)
        write_controured_img(img, [self.__inp_coords, inp_coords_bordered], self.__threshvalue)
    
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
            self.gameplay.start_game()
            pass
        elif message_dict["command"] == consts.MQTT_COMMANDS.PAUSE.value:
            self.gameplay.pause_game()
            pass
        elif message_dict["command"] == consts.MQTT_COMMANDS.STOP.value:
            self.gameplay.stop_game()
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
        
        self.__inp_coords, self.__out_coords, self.__matrix = set_transformation_matrix(self.__global_data, coordinates)
        bordered_matrix, inp_coords_bordered = get_transformation_matrix_with_borders(self.__inp_coords, self.__out_coords, self.__global_data.img_resize)
        self.__reference_blur, self.__threshvalue, img = set_compare_values(self.__takePicture, self.__matrix, bordered_matrix, self.__global_data.window_size, self.__logger)
        write_controured_img(img, [self.__inp_coords, inp_coords_bordered], self.__threshvalue)

    @change_actions_decorator
    def __flip_view(self):
        self.__global_data.is_spin = not self.__global_data.is_spin
        self.gameplay.spin_words()

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

            self.gameplay.game_loop()

            pygame.display.update()
            self.__clock.tick(consts.CLOCK)
            self.__counter+=1

            self.__event_handler()
