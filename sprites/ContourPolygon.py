import cv2
import pygame
import numpy as np
from random import randint
from utils.consts import *
from utils.internals_management_helpers import createFishSprite, checkCollision

class ContourPolygon(pygame.sprite.Sprite):
    def __init__(self, contour, resize_proportion):
        super().__init__()
        self.resize_proportion = resize_proportion
        self.contour_color = (randint(0,255),randint(0,255),randint(0,255))
        self.color = (10,10,10)
        self.__setShape(contour)
        self.internal_sprites = pygame.sprite.Group()

        self.decideHowManyKids()

    def updateShape(self, contour):
        self.__setShape(contour)
        return self
    
    def decideHowManyKids(self):
        if not hasattr(self, 'internal_sprites'):
            self.internal_sprites = pygame.sprite.Group()
        
        internal_amount = len(self.internal_sprites.sprites())
        avg_fish_width = np.average(FISH_SIZE_WIDTH_RANGE)
        wanted_amount = int(self.area/((avg_fish_width**2)*FREE_AREA_FOR_FISH))

        # if (internal_amount > wanted_amount):
        #     for i in range(wanted_amount, internal_amount):
        #         self.internal_sprites.sprites()[i].kill()
        # elif internal_amount < wanted_amount:
        if internal_amount < wanted_amount:
            for i in range(internal_amount, wanted_amount):
                sp = self.__FishSprite()
                if sp:
                    self.internal_sprites.add(sp)
    
    def __FishSprite(self):
        return createFishSprite(self.inv_mask, (self.rect.width, self.rect.height))

    def __setShape(self, contour): 
        bounding = list(map(lambda x: int(x * self.resize_proportion), cv2.boundingRect(contour)))
        x = bounding[BOUND_LEGEND["X"]]
        y = bounding[BOUND_LEGEND["Y"]]
        points = [(int(point[0][0] * self.resize_proportion) - x, int(point[0][1] * self.resize_proportion) - y) for point in contour]

        self.image = pygame.Surface((bounding[BOUND_LEGEND["WIDTH"]], bounding[BOUND_LEGEND["HEIGHT"]]), pygame.SRCALPHA)
        self.rect = pygame.draw.polygon(self.image, self.color, points)
        self.mask = pygame.mask.from_threshold(self.image, self.color, threshold=(1, 1, 1))
        self.inv_mask = pygame.mask.from_threshold(self.image, self.color, threshold=(1, 1, 1))
        pygame.mask.Mask.invert(self.inv_mask)

        self.contour = contour
        self.area = cv2.contourArea(contour)
        self.rect.x = x
        self.rect.y = y
        self.rect.height = bounding[BOUND_LEGEND["HEIGHT"]]
        self.rect.width = bounding[BOUND_LEGEND["WIDTH"]]

        # self.decideHowManyKids()

    def update(self):
        checkCollision(self.internal_sprites, self.inv_mask, (self.rect.width, self.rect.height))
        self.internal_sprites.update()
        self.internal_sprites.draw(self.image)

