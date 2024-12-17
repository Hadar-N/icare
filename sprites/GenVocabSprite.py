import pygame
from random import randint, uniform
import time
from utils.consts import *
from utils.dataSingleton import DataSingleton

class GenVocabSprite(pygame.sprite.Sprite):
    def __init__(self, vocab_i, property):
        super().__init__()

        self._global_data = DataSingleton()
        self._vocab = self._global_data.vocab_options[vocab_i]
        self._color = (0,0,255) if property == "en" else (255,0,0)
        self._floatlocation = (0.,0.)

        self.image = pygame.transform.flip(self._global_data.vocab_font.render(self._vocab[property], True, self._color), True, False)
        self.rect = self.image.get_rect()

        self.mask = pygame.mask.from_surface(self.image)
        pygame.mask.Mask.invert(self.mask)
        self.area = self.mask.count()

        # color = (255,0,0)
        # for x in range(int(self.rect.width)):
        #     for y in range(int(self.rect.height)):
        #         if self.mask.get_at((x,y)) != 0:
        #             self.image.set_at((x,y), color)
            
    @property
    def vocabEN(self): return self._vocab["en"]
    @property
    def vocabZH(self): return self._vocab["zh"]
    @property
    def isOutOfBounds(self): return any([self._floatlocation[i] < 0 or self._floatlocation[i] + self.rect[2+i] > self._global_data.window_size[i] for i in range(0,2)])
    
    def matchSuccess(self):
        self.kill()

    def setLocation(self, coordinates):
        self._floatlocation = coordinates
        self.rect.x, self.rect.y = self._floatlocation

    def onCollision(self, area):
        raise NotImplementedError("method not implemented")

