import pygame
from random import randint, uniform
import time
import subprocess

from utils.consts import *
from utils.dataSingleton import DataSingleton
from .GenVocabSprite import GenVocabSprite

class VocabENSprite(GenVocabSprite):
    def __init__(self, vocab_i):
        super().__init__(vocab_i, "en")

        self.__is_presented = False
            
    @property
    def isPresented(self): return self.__is_presented
    @property
    def isOutOfBounds(self): return False

    def onCollision(self, area_collision):
        new_presented = area_collision<self.area/4

        if new_presented and not self.__is_presented:
            self._global_data.espeak_engine.say(f'{self._vocab["en"]} .')
            self._global_data.espeak_engine.runAndWait()
        
        self.__is_presented = new_presented