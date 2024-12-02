import pygame
from random import randint, uniform
import math
from utils.consts import *
import time
from utils.dataSingleton import DataSingleton
from .GenVocabSprite import GenVocabSprite

# Structure instructions:
# zh vocab will be divided into 2 groups:
# 1. bank (all ZH versions of existing EN vocab)
# 2. active group- currently on the screen
# and each zh vocan is in one (or no) group at a time:
# - if it is not-yet matched and not currently on screen: should be in "bank"
# - if it is currently on screen (aka not matched yet): should be in "active"
# - if it is already matched: should be "kill"ed (aka in no group)

class VocabZHSprite(GenVocabSprite):
    def __init__(self, vocab_i, bank):
        super().__init__(vocab_i, "zh")

        self. __bank_group = bank
        self.__appearing = 0.0
        self.__deleting = False
        self.__flip_times = [time.time()]

        self.__time_for_direction_change = randint(50,120)
        self.__dir_time = 0
        self.__direction = None

        self.__randomizeDirection()
        self.__setAlpha()
    
    @property
    def isDeleting(self): return self.__deleting

    def __randomizeDirection(self):
        if self.__deleting:
            return
        elif self.__dir_time <= 0:
            self.__dir_time = self.__time_for_direction_change
            self.__direction = self.__randomizeAngle()
        else:
            self.__dir_time-=1

    def __randomizeAngle(self):
        res=None
        if self.__direction:
            angle_change = uniform(-1*FISH_ANGLE_MAX_DIFF, FISH_ANGLE_MAX_DIFF)
            res = self.__direction.rotate(angle_change)
        else: res = pygame.math.Vector2(uniform(-1*FISH_MAX_SPEED, FISH_MAX_SPEED), uniform(-1*FISH_MAX_SPEED, FISH_MAX_SPEED))
        if res.length() < 1: res.normalize()*uniform(1,FISH_MAX_SPEED)
        print(f'{self.vocabZH} new direction: ', res, res.length())
        return res
    
    def flipDirection(self):
        if self.__deleting:
            return

        self.__direction = self.__direction.rotate(180)

        last_item = self.__flip_times.pop()
        curr = time.time()
        if curr - last_item < 1: [self.removeSelf(True) if len(self.__flip_times) > FISH_STUCK_THRESH else self.__flip_times.extend((last_item, curr))]
        else:
            self.__flip_times = [curr]
            self.__dir_time = self.__time_for_direction_change
        
    def removeSelf(self, is_collision = False):
        self.__deleting=True
        if is_collision: self.__direction = pygame.math.Vector2(0,0)
    
    def __setAlpha(self):
        self.image.set_alpha(self.__appearing*FISH_MAX_OPACITY)
        if (self.__deleting):
            self.__appearing -=FISH_APPEAR_SPEED
            if self.__appearing <= 0.0:
                self.kill()
                self.__bank_group.add(self)
                self.__deleting = False
        elif (self.__appearing < 1.0): self.__appearing = 1.0 if self.__appearing+FISH_APPEAR_SPEED > 1.0 else self.__appearing+FISH_APPEAR_SPEED

    def update(self):
        self.rect.x += round(self.__direction[0])
        self.rect.y += round(self.__direction[1])

        self.__setAlpha()
        self.__randomizeDirection()

