import pygame
from random import randint, uniform
import math
import numpy as np
import time

from game_shared import MQTT_DATA_ACTIONS
from mqtt_shared import Topics

from utils import DataSingleton
from utils.consts import *
from .gen_vocab_sprite import GenVocabSprite

# Structure instructions:
# zh vocab will be divided into 2 groups:
# 1. bank (all ZH versions of existing EN vocab)
# 2. active group- currently on the screen
# and each zh vocan is in one (or no) group at a time:
# - if it is not-yet matched and not currently on screen: should be in "bank"
# - if it is currently on screen (aka not matched yet): should be in "active"
# - if it is already matched: should be "kill"ed (aka in no group)

class OptionVocabSprite(GenVocabSprite):
    def __init__(self, vocab, eventbus):
        super().__init__(vocab, eventbus)

        self.__appearing = 0.0
        self.__deleting = False
        self.__flip_times = [time.time()]

        self.__direction = None
        self.__rng = np.random.default_rng() # scale for random() = [-4,4]

        self.__randomize_direction()
        self.__set_alpha()
    
    @property
    def vocabSelf(self): return self.vocabTranslation
    @property
    def is_deleting(self): return self.__deleting
    @property
    def _get_color(self): return (255,0,0)

    def __randomize_direction(self):
        if self.__deleting:
            return
        else:
            self.__direction = self.__randomize_angle()

    def __randomize_sign(self): return -1 if randint(0,1) else 1

    def __randomize_angle(self):
        res=None
        if self.__direction:
            change_course = self.__rng.normal()
            res = self.__direction.rotate(change_course*(SPRITE_ANGLE_MAX_DIFF/4)) if change_course > 0.5 else self.__direction
            if res.length() < 1: res.normalize()*uniform(SPRITE_MIN_SPEED,SPRITE_MAX_SPEED)
        else: res = pygame.math.Vector2(self.__randomize_sign()*uniform(SPRITE_MIN_SPEED, SPRITE_MAX_SPEED), self.__randomize_sign()*uniform(SPRITE_MIN_SPEED, SPRITE_MAX_SPEED))
        return res
    
    def test_match(self):
        if self.vocabTranslation == self.twin.vocabTranslation:
            self._eventbus.publish(Topics.word_state(), {"type": MQTT_DATA_ACTIONS.MATCHED, "word": self.as_dict()})
            self.match_success()
        else:
            self.twin.turn_option_off(self.vocabTranslation)
            self._eventbus.publish(Topics.word_state(), {"type": MQTT_DATA_ACTIONS.STATUS, "word": self.twin.as_dict()})
            self.twin = None
            self.kill()
            
    
    def on_collision(self, area_collision: int):
        if area_collision: self.flip_direction()
        return None
    
    def flip_direction(self):
        if self.__deleting:
            return

        self.__direction = self.__direction.rotate(180)

        last_item = self.__flip_times.pop()
        curr = time.time()
        if curr - last_item < 1: [self.remove_self(True) if len(self.__flip_times) > SPRITE_STUCK_THRESH else self.__flip_times.extend((last_item, curr))]
        else:
            self.__flip_times = [curr]
        
    def remove_self(self, is_collision = False):
        self.__deleting=True
        if is_collision: self.__direction = pygame.math.Vector2(0,0)
    
    def __set_alpha(self):
        self.image.set_alpha(self.__appearing*SPRITE_MAX_OPACITY)
        if (self.__deleting):
            self.__appearing -=SPRITE_APPEAR_SPEED
            if self.__appearing <= 0.0:
                self.kill()
                self.__deleting = False
        elif (self.__appearing < 1.0): self.__appearing = 1.0 if self.__appearing+SPRITE_APPEAR_SPEED > 1.0 else self.__appearing+SPRITE_APPEAR_SPEED

    def update(self):
        self._floatlocation = [self._floatlocation[i]+self.__direction[i] for i in range(0,2)]
        self.rect.x, self.rect.y = self._floatlocation

        self.__set_alpha()
        self.__randomize_direction()

