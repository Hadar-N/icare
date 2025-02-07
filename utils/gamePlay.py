import os
import cv2
import pygame
import numpy as np
from logging import Logger

import utils.consts as consts
from utils.eventBus import EventBus
from utils.dataSingleton import DataSingleton
from utils.vocab_interaction_helpers import checkCollision, vocabMatching
from utils.vocab_management_helpers import initVocabOptions, AddVocabToGroup, vocabReadMaskCollision, presentNewZHVocab

class GamePlay():
    def __init__(self, takePicture, window: pygame.Surface, matrix: np.ndarray, logger: Logger, threshval: np.float64, ref_img: np.ndarray, eventbus : EventBus):

        self._global_data = DataSingleton()
        self._takePicture = takePicture
        self._logger = logger
        self._window = window
        self._matrix = matrix
        self._threshval = threshval
        self._ref_img = ref_img
        self._kernel = np.ones((11, 11), np.uint8)  # Larger kernel for more aggressive closing
        self._eventbus = eventbus
        eventbus.subscribe(consts.MQTT_TOPIC_CONTROL, self.handle_control_command)

        self._mask = self._area = None
        self._isrun = False

        self._vocabengroup = pygame.sprite.Group()
        self._vocabzhbankgroup = pygame.sprite.Group()
        self._vocabzhdrawgroup = pygame.sprite.Group()

    def __initGame(self):
        initVocabOptions()
        self._vocabengroup.empty()
        self._vocabzhbankgroup.empty()
        self._vocabzhdrawgroup.empty()
        AddVocabToGroup(self._vocabengroup, self._vocabzhbankgroup)

        self._isrun=True

    def __renewCameraPicture(self, counter):
        if (counter%(consts.CLOCK/2) == 0 or not self._mask or not self._area):
            image = cv2.resize(self._takePicture(), self._global_data.img_resize)
            image = cv2.flip(cv2.warpPerspective(image, self._matrix,  (self._global_data.window_size[1], self._global_data.window_size[0]) ,flags=cv2.INTER_LINEAR), 0)

            mask_img = self.__createMask(image)
            mask_img = cv2.bitwise_not(mask_img)

            mask_img_rgb = pygame.surfarray.make_surface(cv2.cvtColor(mask_img, cv2.COLOR_GRAY2RGB))
            self._mask = pygame.mask.from_threshold(mask_img_rgb, (0,0,0), threshold=(1,1,1))
            self._area = (self._global_data.window_size[0] * self._global_data.window_size[1]) - self._mask.count()

    def __createMask(self, current_image):
        current_blurred = cv2.GaussianBlur(current_image, consts.BLUR_SIZE, 0)
        difference = cv2.absdiff(current_blurred, self._ref_img)
        gray_image = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
        _, thresholded = cv2.threshold(gray_image, self._threshval, consts.THRESHOLD_MAX, cv2.THRESH_BINARY_INV)
        closed = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, self._kernel)
        return closed
    
    def handle_control_command(self, command):
        print("handle_control_command!!!", command)
        if command == consts.MQTT_COMMANDS.START.value:
            self.start_game()
            pass
        elif command == consts.MQTT_COMMANDS.PAUSE.value:
            self.pause_game()
            pass
        elif command == consts.MQTT_COMMANDS.STOP.value:
            self.stop_game()
            pass

    def start_game(self):
        if(len(self._vocabengroup.sprites())):
            self._isrun = True
        else:
            self.__initGame()

    def pause_game(self):
        self._isrun = False

    def stop_game(self):
        self._isrun = False
        self._vocabengroup.empty()
        self._vocabzhbankgroup.empty()
        self._vocabzhdrawgroup.empty()

    def game_loop(self, counter):
        if self._isrun:
            self.__renewCameraPicture(counter)

            vocabMatching(self._logger, self._vocabengroup, self._vocabzhdrawgroup, self._eventbus)
            
            presentNewZHVocab(self._vocabzhbankgroup, self._vocabzhdrawgroup, self._mask, self._area)
            checkCollision(self._vocabzhdrawgroup, self._mask)
            vocabReadMaskCollision(self._vocabengroup, self._mask)

            self._vocabzhdrawgroup.update()
            self._vocabzhdrawgroup.draw(self._window)
            self._vocabengroup.draw(self._window)