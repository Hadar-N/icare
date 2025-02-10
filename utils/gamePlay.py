import os
import cv2
import pygame
import json
import pyttsx3
import numpy as np
from logging import Logger
from random import randint, sample

import utils.consts as consts
from utils.eventBus import EventBus
from utils.dataSingleton import DataSingleton
from sprites.VocabENSprite import VocabENSprite
from sprites.VocabZHSprite import VocabZHSprite

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

        self._vocabengroup = pygame.sprite.Group()
        self._vocabzhbankgroup = pygame.sprite.Group()
        self._vocabzhdrawgroup = pygame.sprite.Group()

        self._mask = self._area = None
        self._isrun = False


    def __initGame(self):
        self.__initVocabOptions()
        self._vocabengroup.empty()
        self._vocabzhbankgroup.empty()
        self._vocabzhdrawgroup.empty()
        self.__AddVocabToGroup()

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
    
    def __initVocabOptions(self):
        self._global_data.vocab_font = pygame.font.Font(consts.FONT_PATH, consts.FONT_SIZE)
        self._global_data.espeak_engine = pyttsx3.init(driverName='espeak') if self._global_data.env == "pi" else pyttsx3.init()

        with open(consts.VOCAB_PATH, 'r', encoding="utf8") as file:
            data = json.load(file)
            self._global_data.vocab_options = sample(data, consts.VOCAB_AMOUNT)

    def __AddVocabToGroup(self):
        for i in range(consts.VOCAB_AMOUNT):
            ENvocab = VocabENSprite(i)
            placement = self.__randomizeVacantLocation(ENvocab, self._vocabengroup)
            if (placement):
                self._vocabengroup.add(ENvocab)
                self._vocabzhbankgroup.add(VocabZHSprite(i, self._vocabzhbankgroup))
            else: ENvocab.kill()

    def __presentNewZHVocab(self):
        amount_per_space = round(self._area / ((self._global_data.window_size[0]*self._global_data.window_size[1])/(consts.MAX_VOCAB_ACTIVE*2)))
        amount_per_space = amount_per_space if amount_per_space < consts.MAX_VOCAB_ACTIVE else consts.MAX_VOCAB_ACTIVE
        
        if len(self._vocabzhdrawgroup.sprites()) < amount_per_space and len(self._vocabzhbankgroup.sprites()):
            temp = self._vocabzhbankgroup.sprites()[0]
            placement = self.__randomizeVacantLocation(temp)

            if (placement):
                self._vocabzhdrawgroup.add(temp)
                temp.remove(self._vocabzhbankgroup)

    def __random_location(self, sprite):
        return randint(consts.CLEAN_EDGES, self._global_data.window_size[0] - consts.CLEAN_EDGES - sprite.rect.width), randint(consts.CLEAN_EDGES, self._global_data.window_size[1] - consts.CLEAN_EDGES - sprite.rect.height)

    def __randomizeVacantLocation(self, sprite, group=None):
        def locationCondition(rect): 
            return pygame.sprite.spritecollide(sprite, group, False) if type(group) == pygame.sprite.Group else self._mask.overlap(sprite.mask, (rect.x,rect.y))

        count = consts.MAX_PLACEMENT_ATTAMPTS
        sprite.setLocation(self.__random_location(sprite))
        
        while locationCondition(sprite.rect) and count > 0:
            sprite.setLocation(self.__random_location(sprite))
            count-=1

        return True if count > 0 else False

    def __checkCollision(self, group):
        for sp in group.sprites():
            if sp.isOutOfBounds:
                sp.onCollision(True)
                continue
            
            overlap_area = self._mask.overlap_area(sp.mask, (sp.rect.x, sp.rect.y))
            sp.onCollision(overlap_area)

    def __vocabMatching(self): 
        for sp in self._vocabzhdrawgroup.sprites():
            collides = pygame.sprite.spritecollide(sp,self._vocabengroup,False)
            if collides:
                relevant = next((c_sp for c_sp in collides if c_sp.vocabZH == sp.vocabZH and c_sp.vocabEN == sp.vocabEN), None)
                if relevant:
                    self.__eventbus.publish(consts.MQTT_TOPIC_DATA, {'word': {'zh': sp.vocabZH, 'en': relevant.vocabEN}})
                    relevant.matchSuccess()
                    sp.matchSuccess()
                    self._logger.info(f'disappeared word: {sp.vocabZH}/{relevant.vocabEN}; left words: {len(self._vocabengroup.sprites())}')
                    if len(self._vocabengroup.sprites()) == 0: self.__finishGame()

    def __finishGame(self):
        self._logger.info("game finished!")
        self.__eventbus.publish(consts.MQTT_TOPIC_DATA, {'status': 'finished'})
        print("finished!!!")

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

            self.__vocabMatching()
            
            self.__presentNewZHVocab()
            self.__checkCollision(self._vocabzhdrawgroup)
            self.__checkCollision(self._vocabengroup)

            self._vocabzhdrawgroup.update()
            self._vocabzhdrawgroup.draw(self._window)
            self._vocabengroup.draw(self._window)