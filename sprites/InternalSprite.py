import pygame
from random import randint, uniform
import math
from utils.consts import *
import time

class InternalSprite(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__()

        orig_rect = image.get_rect()
        ideal_width = randint(FISH_SIZE_WIDTH_RANGE[0], FISH_SIZE_WIDTH_RANGE[1])
        ideal_height = (orig_rect[BOUND_LEGEND["HEIGHT"]]/orig_rect[BOUND_LEGEND["WIDTH"]])*ideal_width

        self.orig_image = pygame.transform.scale(image, (ideal_width, ideal_height))
        self.image = pygame.Surface((ideal_width + FISH_BORDER*2, ideal_height + FISH_BORDER*2), pygame.SRCALPHA)
        self.image.blit(self.orig_image, (FISH_BORDER, FISH_BORDER))
        self.rect = self.image.get_rect()

        self.__appearing = FISH_APPEAR_SPEED
        self.__deleting = False
        self.__flip_times = [time.time()]

        self.__time_for_direction_change = randint(100,250)
        self.__dir_time = 0
        self.__base_dir = pygame.math.Vector2(1, 0)
        self.__direction = None

        self.__randomizeDirection()

        # color = FISH_COLOR
        # for x in range(int(self.rect.width)):
        #     for y in range(int(self.rect.height)):
        #         if self.mask.get_at((x,y)) != 0:
        #             self.image.set_at((x,y), color)

        self.__setFishAlpha()
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
            self.__rotateFishImage()
        else:
            self.__dir_time-=1
    
    def flipDirection(self):
        if self.__deleting:
            return

        self.__direction = self.__direction.rotate(180)
        self.__rotateFishImage()

        last_item = self.__flip_times.pop()
        curr = time.time()
        if curr - last_item < 1: [self.removeSelf(True) if len(self.__flip_times) > FISH_STUCK_THRESH else self.__flip_times.extend((last_item, curr))]
        else: self.__flip_times = [curr]
        
    def removeSelf(self, is_collision = False):
        self.__deleting=True
        if is_collision: self.__direction = pygame.math.Vector2(0,0)
    
    def __rotateFishImage(self):
        angle = self.__direction.angle_to(self.__base_dir)
        self.image = pygame.transform.rotate(self.orig_image, angle)
        new_rect = self.image.get_rect()
        new_rect.x, new_rect.y, _, _ = self.rect
        self.rect = new_rect
        self.mask = pygame.mask.from_surface(self.image)
        pygame.mask.Mask.invert(self.mask)

    def __setFishAlpha(self):        
        self.image.set_alpha(FISH_MAX_OPACITY-(self.__appearing/FISH_APPEAR_SPEED)*FISH_MAX_OPACITY)
        if (self.__deleting):
            self.__appearing +=1
            if self.__appearing == 255: self.kill()
        elif (self.__appearing): self.__appearing -=1

    
    def update(self):
        self.rect.x += self.__direction[0]
        self.rect.y += self.__direction[1]

        self.__setFishAlpha()
        self.__randomizeDirection()

