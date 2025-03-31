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

class OptionVocabSprite(GenVocabSprite):
    def __init__(self, vocab, eventbus):
        super().__init__(vocab, eventbus)
    
    @property
    def vocabSelf(self): return self.vocabTranslation
    @property
    def _get_color(self): return (255,0,255)
    
    def test_match(self):
        if self.vocabTranslation == self.twin.vocabTranslation:
            self._eventbus.publish(Topics.word_state(), {"type": MQTT_DATA_ACTIONS.MATCHED, "word": self.as_dict()})
            self.match_success()
        else:
            self.twin.turn_option_off(self.vocabTranslation)
            self._eventbus.publish(Topics.word_state(), {"type": MQTT_DATA_ACTIONS.STATUS, "word": self.twin.as_dict()})
            self.twin = None
            self.kill()
            