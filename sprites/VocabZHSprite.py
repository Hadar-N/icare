import pygame
from random import randint, uniform
import math
from utils.consts import *
import time
from utils.dataSingleton import DataSingleton

# Structure instructions:
# zh vocab will be divided into 2 groups:
# 1. bank (all ZH versions of existing EN vocab)
# 2. active group- currently on the screen
# and each zh vocan is in one (or no) group at a time:
# - if it is not-yet matched and not currently on screen: should be in "bank"
# - if it is currently on screen (aka not matched yet): should be in "active"
# - if it is already matched: should be "kill"ed (aka in no group)

class VocabZHSprite(pygame.sprite.Sprite):
    def __init__(self, vocab_i, bank):
        super().__init__()

        self.__global_data = DataSingleton()
        self.__vocab = self.__global_data.vocab_options[vocab_i]

        self.image = pygame.transform.flip(self.__global_data.vocab_font.render(self.__vocab["zh"], True, (255,0,0)), True, False)        
        self.rect = self.image.get_rect()

        # self.interval = 0
        self. __bank_group = bank
        self.__appearing = 0.0
        self.__deleting = False
        self.__flip_times = [time.time()]

        self.__time_for_direction_change = randint(100,250)
        self.__dir_time = 0
        self.__direction = None

        self.__randomizeDirection()


        # color = FISH_COLOR
        # for x in range(int(self.rect.width)):
        #     for y in range(int(self.rect.height)):
        #         if self.mask.get_at((x,y)) != 0:
        #             self.image.set_at((x,y), color)

        self.__setAlpha()
        self.mask = pygame.mask.from_surface(self.image)
        pygame.mask.Mask.invert(self.mask)
        self.area = self.mask.count()
        
    def __randomizeDirection(self):
        if self.__deleting:
            return
        elif self.__dir_time <= 0:
            self.__dir_time = self.__time_for_direction_change
            if self.__direction:
                angle_change = uniform(-FISH_ANGLE_MAX_DIFF, FISH_ANGLE_MAX_DIFF)
                self.__direction = self.__direction.rotate(angle_change)
            else: self.__direction = pygame.math.Vector2(uniform(-1*FISH_MAX_SPEED, FISH_MAX_SPEED), uniform(-1*FISH_MAX_SPEED, FISH_MAX_SPEED))
        else:
            self.__dir_time-=1
    
    def flipDirection(self):
        if self.__deleting:
            return

        self.__direction = self.__direction.rotate(180)

        last_item = self.__flip_times.pop()
        curr = time.time()
        if curr - last_item < 1: [self.removeSelf(True) if len(self.__flip_times) > FISH_STUCK_THRESH else self.__flip_times.extend((last_item, curr))]
        else: self.__flip_times = [curr]
        
    def removeSelf(self, is_collision = False):
        self.__deleting=True
        print('starting to kill self: ', self.vocabZH)
        if is_collision: self.__direction = pygame.math.Vector2(0,0)
    
    def __setAlpha(self):
        self.image.set_alpha(self.__appearing*FISH_MAX_OPACITY)
        if (self.__deleting):
            self.__appearing -=FISH_APPEAR_SPEED
            if self.__appearing <= 0.0:
                self.kill()
                self.__bank_group.add(self)
                print('just killed self: ', self.vocabZH)
        elif (self.__appearing < 1.0): self.__appearing = 1.0 if self.__appearing+FISH_APPEAR_SPEED > 1.0 else self.__appearing+FISH_APPEAR_SPEED

    def matchSuccess(self):
        self.kill()

    @property
    def isDeleting(self): return self.__deleting
    @property
    def vocabEN(self): return self.__vocab["en"]
    @property
    def vocabZH(self): return self.__vocab["zh"]
    @property
    def isPresented(self): return self.__is_presented

    def update(self):
        self.rect.x += self.__direction[0]
        self.rect.y += self.__direction[1]

        self.__setAlpha()
        self.__randomizeDirection()

