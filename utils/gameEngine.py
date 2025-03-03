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

class GameEngine():
    def __init__(self, logger: Logger, eventbus: EventBus, takePicture):

        self.__state= consts.GAME_STATES.INIT

        self.__running = True
        self.__counter = 0
        self.__logger = logger
        self.__eventbus = eventbus
        self.__eventbus.subscribe(consts.MQTT_TOPIC_CONTROL, self.__handle_control_command)
        self.__takePicture = takePicture
        self.__matrix = self.__threshvalue = self.__reference_blur= None
        self.__global_data = DataSingleton()
        self.__clock = pygame.time.Clock()

        self.__window = self.__setup_window()
        self.__setup_comparison_data()

        self.__gameplay = GamePlay(self.__window, self.__logger, self.__eventbus, self.__get_image_for_game)

        self.__state= consts.GAME_STATES.ACTIVE

    @property
    def state(self): return self.__state

    def __handle_control_command(self, message):
        message_dict = json.loads(message)
        print("handleControlCommand: ", message_dict)
        if message_dict["command"] == consts.MQTT_COMMANDS.START.value:
            self.__gameplay.startGame()
            pass
        elif message_dict["command"] == consts.MQTT_COMMANDS.PAUSE.value:
            self.__gameplay.pauseGame()
            pass
        elif message_dict["command"] == consts.MQTT_COMMANDS.STOP.value:
            self.__gameplay.stopGame()
            pass
        elif message_dict["command"] == consts.MQTT_COMMANDS.FLIP_VIEW.value:
            """ TODO """
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
            print("new image~", mask, area)
            return mask, area

    def __createMask(self, current_image):
        current_blurred = cv2.GaussianBlur(current_image, consts.BLUR_SIZE, 0)
        difference = cv2.absdiff(current_blurred, self.__reference_blur)
        gray_image = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
        _, thresholded = cv2.threshold(gray_image, self.__threshvalue, consts.THRESHOLD_MAX, cv2.THRESH_BINARY_INV)
        closed = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, consts.KERNEL)
        return closed

    def __setup_comparison_data(self):
        self.__set_transformation_matrix()

        self.__window.fill((0, 0, 0))
        pygame.display.update()
        time.sleep(2)

        self.__set_compare_values()

    def __reset_comparison_data(self, coordinates):
        self.__state= consts.GAME_STATES.HALTED
        self.__gameplay.pauseGame()
        if(not coordinates or len(coordinates) is not 4):
            print('invalid coordinates!', type(coordinates), coordinates)
            return
        self.__set_transformation_matrix(coordinates)
        self.__set_compare_values()
        self.__gameplay.startGame()
        self.__state= consts.GAME_STATES.ACTIVE

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

    def __set_transformation_matrix(self, coordinates = None):
        image = self.__takePicture()
        image = cv2.resize(image, self.__global_data.img_resize)
    
        if not coordinates:
            contours = self.__findcontours(image)
            coordinates = self.__findboard(contours)

        ordered_points_in_board = sort_points([item[0] for item in coordinates])
        
        inp =  np.float32(ordered_points_in_board)
        out =  np.float32([[0,0], [0, self.__global_data.window_size[0] - 1], [self.__global_data.window_size[1] - 1, self.__global_data.window_size[0] - 1], [self.__global_data.window_size[1] - 1, 0]])

        self.__matrix = cv2.getPerspectiveTransform(inp, out)

        self.__logger.info(f'contouring data: inp={asstr(inp)}; out={asstr(out)}; matrix={asstr(self.__matrix)}')
        cv2.polylines(image, [inp.astype(np.int32)], isClosed=True, color=(0,255,0), thickness=5)
        cv2.imwrite(consts.CONTOUR_IMAGE_LOC, image)
    
    def __set_compare_values(self):
        image = self.__takePicture()
        image = cv2.resize(image, self.__global_data.img_resize)

        reference_image = cv2.flip(cv2.warpPerspective(image, self.__matrix, (self.__global_data.window_size[1], self.__global_data.window_size[0]) ,flags=cv2.INTER_LINEAR), 0)
        self.__reference_blur = cv2.GaussianBlur(reference_image, consts.BLUR_SIZE, 0)
        self.__threshvalue = self.__findthreshval(self.__reference_blur, 1.2)
        self.__logger.info(f'threshvalue={self.__threshvalue}')

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
            self.__window.fill((0,255,0))

            if self.__state == consts.GAME_STATES.ACTIVE:
                self.__gameplay.gameLoop()
                self.__window.blit(self.__gameplay.mask, (0,0))

            pygame.display.update()
            self.__clock.tick(consts.CLOCK)
            self.__counter+=1

            self.__event_handler()

