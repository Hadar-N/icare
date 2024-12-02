import pygame
from random import randint, uniform
import time
from utils.consts import *
from utils.dataSingleton import DataSingleton

class VocabENSprite(pygame.sprite.Sprite):
    def __init__(self, vocab_i):
        super().__init__()

        self.__global_data = DataSingleton()
        self.__vocab = self.__global_data.vocab_options[vocab_i]

        self.image = pygame.transform.flip(self.__global_data.vocab_font.render(self.__vocab["en"], True, (0,0,255)), True, False)
        self.rect = self.image.get_rect()

        self.__is_presented = False

        self.mask = pygame.mask.from_surface(self.image)
        pygame.mask.Mask.invert(self.mask)
        self.area = self.mask.count()

        # color = (255,0,0)
        # for x in range(int(self.rect.width)):
        #     for y in range(int(self.rect.height)):
        #         if self.mask.get_at((x,y)) != 0:
        #             self.image.set_at((x,y), color)
        
    def removeSelf(self, is_collision = False):
        self.__deleting=True
        if is_collision: self.__direction = pygame.math.Vector2(0,0)

    def changeIsPresented(self, is_collision):
        if (self.__is_presented and is_collision) or (not self.__is_presented and not is_collision):
            self.__is_presented = not self.__is_presented
            if self.__is_presented:
                self.__global_data.espeak_engine.say(f'{self.__vocab["en"]} .')
                self.__global_data.espeak_engine.runAndWait()
    
    @property
    def isDeleting(self): return self.__deleting
    @property
    def vocabEN(self): return self.__vocab["en"]
    @property
    def vocabZH(self): return self.__vocab["zh"]
    @property
    def isPresented(self): return self.__is_presented
    
    def matchSuccess(self):
        self.kill()

    # def update(self):
    #     # self.rect.x += self.__direction[0]
    #     # self.rect.y += self.__direction[1]

    #     self.__setAlpha()
    #     # self.__randomizeDirection()

