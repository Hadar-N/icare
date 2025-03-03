import pygame
import json
import pyttsx3
from logging import Logger
from random import randint, sample

import utils.consts as consts
from utils.eventBus import EventBus
from utils.dataSingleton import DataSingleton
from sprites.VocabENSprite import VocabENSprite
from sprites.VocabZHSprite import VocabZHSprite

class GamePlay():
    def __init__(self, window: pygame.Surface, logger: Logger, eventbus: EventBus, getMask):

        self._global_data = DataSingleton()
        self._logger = logger
        self._window = window

        self._getmask = getMask
        self._eventbus = eventbus

        self._vocabengroup = pygame.sprite.Group()
        self._vocabzhbankgroup = pygame.sprite.Group()
        self._vocabzhdrawgroup = pygame.sprite.Group()

        self._mask = self._area = None
        self.__setupMask(True)
        self._isrun = False

    @property 
    def mask(self): 
        return self._mask.to_surface() if self._mask else pygame.Surface((0,0))
        # return pygame.surfarray.make_surface(self._mask) if self._mask else pygame.Surface((0,0))

    def __setupMask(self, isOverride = False):
        temp = self._getmask(isOverride or not self._mask or self._area is None)
        if temp: self._mask, self._area = temp

    def __initGame(self):
        self.__initVocabOptions()
        self._vocabengroup.empty()
        self._vocabzhbankgroup.empty()
        self._vocabzhdrawgroup.empty()
        self.__AddVocabToGroup()

        self._isrun=True
    
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

    def startGame(self):
        if(len(self._vocabengroup.sprites())):
            self._isrun = True
        else:
            self.__initGame()

    def pauseGame(self):
        self._isrun = False

    def stopGame(self):
        self._isrun = False
        self._vocabengroup.empty()
        self._vocabzhbankgroup.empty()
        self._vocabzhdrawgroup.empty()

    def getStatus(self):
        res = consts.MQTT_STATUSES.ERROR
        if self._isrun: res= consts.MQTT_STATUSES.ONGOING
        elif len(self._vocabengroup.sprites()): res= consts.MQTT_STATUSES.PAUSED
        else: res = consts.MQTT_STATUSES.STOPPED

        return res

    def gameLoop(self):
        if self._isrun:
            self.__setupMask()

            to_publish= self.__vocabMatching()
            
            self.__presentNewZHVocab()
            self.__checkCollision(self._vocabzhdrawgroup)
            to_publish+= self.__checkCollision(self._vocabengroup)

            if len(to_publish): self._eventbus.publish(consts.MQTT_TOPIC_DATA, to_publish)

            self._vocabzhdrawgroup.update()
            self._vocabzhdrawgroup.draw(self._window)
            self._vocabengroup.draw(self._window)