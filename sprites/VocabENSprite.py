import pygame
from random import randint, uniform
import time
from utils.consts import *
from utils.dataSingleton import DataSingleton
from .GenVocabSprite import GenVocabSprite

class VocabENSprite(GenVocabSprite):
    def __init__(self, vocab_i):
        super().__init__(vocab_i, "en")

        self.__is_presented = False
            
    @property
    def isPresented(self): return self.__is_presented
    
    def changeIsPresented(self, is_collision):
        if (self.__is_presented and is_collision) or (not self.__is_presented and not is_collision):
            self.__is_presented = not self.__is_presented
            if self.__is_presented:
                self._global_data.espeak_engine.say(f'{self._vocab["en"]} .')
                self._global_data.espeak_engine.runAndWait()
