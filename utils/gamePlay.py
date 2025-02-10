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
        self._eventbus.subscribe(consts.MQTT_TOPIC_CONTROL, self.handleControlCommand)

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

    def __randomLocation(self, sprite):
        return randint(consts.CLEAN_EDGES, self._global_data.window_size[0] - consts.CLEAN_EDGES - sprite.rect.width), randint(consts.CLEAN_EDGES, self._global_data.window_size[1] - consts.CLEAN_EDGES - sprite.rect.height)

    def __randomizeVacantLocation(self, sprite, group=None):
        def locationCondition(rect): 
            return pygame.sprite.spritecollide(sprite, group, False) if type(group) == pygame.sprite.Group else self._mask.overlap(sprite.mask, (rect.x,rect.y))

        count = consts.MAX_PLACEMENT_ATTAMPTS
        sprite.setLocation(self.__randomLocation(sprite))
        
        while locationCondition(sprite.rect) and count > 0:
            sprite.setLocation(self.__randomLocation(sprite))
            count-=1

        return True if count > 0 else False

    def __checkCollision(self, group):
        to_publish = []
        for sp in group.sprites():
            if sp.isOutOfBounds:
                sp.onCollision(sp.area)
                continue
            
            overlap_area = self._mask.overlap_area(sp.mask, (sp.rect.x, sp.rect.y))
            msg = sp.onCollision(overlap_area)
            if msg: to_publish.append(msg)  
        return to_publish      

    def __vocabMatching(self): 
        matched = []
        for sp in self._vocabzhdrawgroup.sprites():
            collides = pygame.sprite.spritecollide(sp,self._vocabengroup,False)
            if collides:
                relevant = next((c_sp for c_sp in collides if c_sp.vocabZH == sp.vocabZH and c_sp.vocabEN == sp.vocabEN), None)
                if relevant:
                    matched.append({"type": consts.MQTT_DATA_ACTIONS.MATCHED.value, "word": sp.asDict})
                    relevant.matchSuccess()
                    sp.matchSuccess()
                    self._logger.info(f'disappeared word: {sp.vocabZH}/{relevant.vocabEN}; left words: {len(self._vocabengroup.sprites())}')
                    if len(self._vocabengroup.sprites()) == 0: matched.append(self.__finishGame())
        return matched

    def __finishGame(self):
        self._logger.info("game finished!")
        return {"type": consts.MQTT_DATA_ACTIONS.STATUS.value, "word": consts.MQTT_STATUSES.FINISHED.value}

    def handleControlCommand(self, message):
        message_dict = json.loads(message)
        print("handleControlCommand: ", message, message_dict)
        if message_dict["command"] == consts.MQTT_COMMANDS.START.value:
            self.__startGame()
            pass
        elif message_dict["command"] == consts.MQTT_COMMANDS.PAUSE.value:
            self.__pauseGame()
            pass
        elif message_dict["command"] == consts.MQTT_COMMANDS.STOP.value:
            self.__stopGame()
            pass

    def __startGame(self):
        if(len(self._vocabengroup.sprites())):
            self._isrun = True
        else:
            self.__initGame()

    def __pauseGame(self):
        self._isrun = False

    def __stopGame(self):
        self._isrun = False
        self._vocabengroup.empty()
        self._vocabzhbankgroup.empty()
        self._vocabzhdrawgroup.empty()

    def gameLoop(self, counter):
        if self._isrun:
            self.__renewCameraPicture(counter)

            to_publish= self.__vocabMatching()
            
            self.__presentNewZHVocab()
            self.__checkCollision(self._vocabzhdrawgroup)
            to_publish+= self.__checkCollision(self._vocabengroup)

            if len(to_publish): self._eventbus.publish(consts.MQTT_TOPIC_DATA, to_publish)

            self._vocabzhdrawgroup.update()
            self._vocabzhdrawgroup.draw(self._window)
            self._vocabengroup.draw(self._window)