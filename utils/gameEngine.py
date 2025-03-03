import os
import cv2
import pygame
import time
import json
import numpy as np
from logging import Logger

from utils.setup_helpers import asstr, get_img_resize_information, followup_temp, screen_setup, sort_points
import utils.consts as consts
from utils.eventBus import EventBus
from utils.dataSingleton import DataSingleton
from utils.gamePlay import GamePlay


def change_actions_decorator(method):
    def wrapper(self, *args, **kwargs):
        prev_state = self.state
        prev_gamestatus = self.gameplay.getStatus()

        self.state = consts.GAME_STATES.HALTED
        if prev_gamestatus == consts.MQTT_STATUSES.ONGOING:
            self.gameplay.pauseGame()
        
        method(self, *args, **kwargs)

        if prev_gamestatus == consts.MQTT_STATUSES.ONGOING:
            self.gameplay.startGame()
        self.state = prev_state
    
    return wrapper

class GameEngine():
    def __init__(self, logger: Logger, eventbus: EventBus, takePicture):

        self.state= consts.GAME_STATES.INIT

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
        self.__setup_comparison_data(cv2.resize(initial_img, self.__global_data.img_resize))
        self.__eventbus.subscribe(consts.MQTT_TOPIC_CONTROL, self.__handle_control_command)
        self.gameplay = GamePlay(self.__window, self.__logger, self.__eventbus, self.__get_image_for_game)

        self.state= consts.GAME_STATES.ACTIVE

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
    
    def __get_image_for_game(self, is_initial = False):
        if (self.__counter%consts.NEW_IMAGE_INTERVALS == 0 or is_initial):
            image = cv2.resize(self.__takePicture(), self.__global_data.img_resize)
            image = cv2.flip(cv2.warpPerspective(image, self.__matrix,  (self.__global_data.window_size[1], self.__global_data.window_size[0]) ,flags=cv2.INTER_LINEAR), 0)

            mask_img = self.__createMask(image)
            mask_img = cv2.bitwise_not(mask_img)

            mask_img_rgb = pygame.surfarray.make_surface(cv2.cvtColor(mask_img, cv2.COLOR_GRAY2RGB))
            mask = pygame.mask.from_threshold(mask_img_rgb, (0,0,0), threshold=(1,1,1))
            area = (self.__global_data.window_size[0] * self.__global_data.window_size[1]) - mask.count()
            return mask, area

    def __createMask(self, current_image):
        current_blurred = cv2.GaussianBlur(current_image, consts.BLUR_SIZE, 0)
        difference = cv2.absdiff(current_blurred, self.__reference_blur)
        gray_image = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
        _, thresholded = cv2.threshold(gray_image, self.__threshvalue, consts.THRESHOLD_MAX, cv2.THRESH_BINARY_INV)
        closed = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, consts.KERNEL)
        return closed

    def __setup_comparison_data(self, img):
        self.__set_transformation_matrix(img)

        self.__window.fill((0, 0, 0))
        pygame.display.update()
        time.sleep(1)

        self.__set_compare_values()

        cv2.polylines(img, [self.__inp_coords.astype(np.int32)], isClosed=True, color=(self.__threshvalue, self.__threshvalue, self.__threshvalue), thickness=3)
        cv2.imwrite(consts.CONTOUR_IMAGE_LOC, img)
    
    @change_actions_decorator
    def __reset_comparison_data(self, coordinates):
        if(not coordinates or len(coordinates) != 4):
            print('invalid coordinates!', type(coordinates), coordinates)
            return
        
        self.__set_transformation_matrix(coordinates)
        image = self.__set_compare_values()

        cv2.polylines(image, [self.__inp_coords.astype(np.int32)], isClosed=True, color=(self.__threshvalue, self.__threshvalue, self.__threshvalue), thickness=3)
        cv2.imwrite(consts.CONTOUR_IMAGE_LOC, image)

    @change_actions_decorator
    def __flip_view(self):
        self.__global_data.is_spin = not self.__global_data.is_spin
        self.gameplay.spinWords()

    def __findthreshval(self, empty_image, multip):
        return np.mean(np.mean(empty_image, axis=(0,1)), axis=0) * multip
    
    def __findcontours(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        threshval = self.__findthreshval(image, 1)
        _, thresh = cv2.threshold(gray, threshval, consts.THRESHOLD_MAX, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def __findboard(self, conts):
        rects = []

        fake_contour = np.array([[self.__global_data.img_resize[0] - 1, 0], [0,0], [0, self.__global_data.img_resize[1] - 1],
                                 [self.__global_data.img_resize[0] - 1, self.__global_data.img_resize[1] - 1]]).reshape((-1,1,2)).astype(np.int32)
        full_area = cv2.contourArea(fake_contour)
        area_theshold = full_area/consts.MIN_FRAME_CONTENT_PARTITION

        for c in conts:
            epsilon = 0.02 * cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, epsilon, True)
            area= cv2.contourArea(approx)
            if len(approx) == 4 and area > area_theshold and area < full_area:
                rects.append({"cnt": approx, "area": area})

        match len(rects):
            case 0: return fake_contour
            case 1: return rects[0]["cnt"]
            case _: return max(rects, key=lambda c: c["area"])["cnt"]

    def __set_transformation_matrix(self, ref = None):
        coordinates = ref if isinstance(ref, list) else None
        image = ref if isinstance(ref, np.ndarray) else None
    
        if not coordinates:
            contours = self.__findcontours(image)
            coordinates = self.__findboard(contours)

        ordered_points_in_board = sort_points([item[0] for item in coordinates])
        
        self.__inp_coords =  np.float32(ordered_points_in_board)
        self.__out_coords =  np.float32([[0,0], [0, self.__global_data.window_size[0] - 1], [self.__global_data.window_size[1] - 1, self.__global_data.window_size[0] - 1], [self.__global_data.window_size[1] - 1, 0]])

        self.__matrix = cv2.getPerspectiveTransform(self.__inp_coords, self.__out_coords)

        self.__logger.info(f'contouring data: inp={asstr(self.__inp_coords)}; out={asstr(self.__out_coords)}; matrix={asstr(self.__matrix)}')
    
    def __set_compare_values(self):
        image = self.__takePicture()
        image = cv2.resize(image, self.__global_data.img_resize)

        reference_image = cv2.flip(cv2.warpPerspective(image, self.__matrix, (self.__global_data.window_size[1], self.__global_data.window_size[0]) ,flags=cv2.INTER_LINEAR), 0)
        self.__reference_blur = cv2.GaussianBlur(reference_image, consts.BLUR_SIZE, 0)
        self.__threshvalue = self.__findthreshval(self.__reference_blur, consts.LIGHT_SENSITIVITY_FACTOR)
        self.__logger.info(f'threshvalue={self.__threshvalue}')

        return image

    def __setup_window(self):
        pygame.init()
        pygame.font.init()

        self.__global_data.img_resize = get_img_resize_information()
        window_size, isfullscreen = screen_setup(self.__global_data.img_resize, os.getenv('PROJECTOR_RESOLUTION') if os.environ["DISPLAY"] == ":0" else None, self.__logger)
        self.__global_data.window_size = window_size
        window = pygame.display.set_mode(self.__global_data.window_size, pygame.FULLSCREEN if isfullscreen else 0)

        return window
    
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

            if self.state == consts.GAME_STATES.ACTIVE:
                self.gameplay.gameLoop()

            pygame.display.update()
            self.__clock.tick(consts.CLOCK)
            self.__counter+=1

            self.__event_handler()
