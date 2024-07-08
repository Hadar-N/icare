import cv2
import pygame
import utils.consts as consts
from utils.helpers import getRandomColor
import numpy as np
from random import randint
import math

class ContourPolygon(pygame.sprite.Sprite):
    def __init__(self, contour):
        super().__init__()
        self.color = [getRandomColor(), getRandomColor(), getRandomColor()]
        self.setShape(contour)
        self.internal_sprites = pygame.sprite.Group()

        sp = self.newInternalSprite()
        if sp:
            self.internal_sprites.add(sp)

    def isSpriteBigEnoughToHaveInternal(self):
        w,h = consts.FISH_SIZE
        return self.rect.height > h and self.rect.width > w

    def updateShape(self, contour):
        self.setShape(contour)
        return self
    
    def newInternalSprite(self):
        if not self.isSpriteBigEnoughToHaveInternal():
            return None

        sprite = InternalSprite(consts.FISH_SIZE)
        placement = self.randomizeInternalLocation(sprite)
        if (placement):
            sprite.rect.x, sprite.rect.y = placement
        else:
            return None

        return sprite

    def setShape(self, contour):
        bounding = cv2.boundingRect(contour)
        self.image = pygame.Surface((bounding[consts.BOUND_LEGEND["WIDTH"]], bounding[consts.BOUND_LEGEND["HEIGHT"]]), pygame.SRCALPHA)
        x = bounding[consts.BOUND_LEGEND["X"]]
        y = bounding[consts.BOUND_LEGEND["Y"]]
        points = [(point[0][0] - x, point[0][1] - y) for point in contour]
        self.rect = pygame.draw.polygon(self.image, self.color, points)
        self.mask = pygame.mask.from_threshold(self.image, self.color, threshold=(1, 1, 1))
        self.inv_mask = pygame.mask.from_threshold(self.image, self.color, threshold=(1, 1, 1))
        pygame.mask.Mask.invert(self.inv_mask)

        self.contour = contour
        self.area = cv2.contourArea(contour)
        self.rect.x = x
        self.rect.y = y
        self.rect.height = bounding[consts.BOUND_LEGEND["HEIGHT"]]
        self.rect.width = bounding[consts.BOUND_LEGEND["WIDTH"]]

    def randomizeInternalLocation(self, sprite):
        def random_location():
            random_x = randint(0, int(math.floor(self.rect.width - sprite.rect.height)))
            random_y = randint(0, int(math.floor(self.rect.height - sprite.rect.width)))
            return (random_x, random_y)

        x,y = random_location()

        count = consts.MAX_PLACEMENT_ATTAMPTS
        while self.inv_mask.overlap(sprite.mask, (x, y)) and count > 0:
        # # while self.opmask_surf.get_at((x,y))[0] != 0:
            x,y = random_location()
            count-=1

        return (x,y) if count > 0 else None
        # return (x,y)

    def update(self):
        if pygame.mouse.get_pos():
            for sp in self.internal_sprites:

                dot = self.inv_mask.overlap(sp.mask, (sp.rect.x, sp.rect.y))
                isOutOfBounds = sp.rect.x < 0 or sp.rect.y < 0 or sp.rect.x + sp.rect.width > self.rect.width or sp.rect.y + sp.rect.height > self.rect.height
                if dot or isOutOfBounds:
                    sp.flipDirection()

            self.internal_sprites.update()
            self.internal_sprites.draw(self.image)


class InternalSprite(pygame.sprite.Sprite):
    def __init__(self, size):
        super().__init__()
        self.image = pygame.image.load("utils\\location.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, size)
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.DIRECTION_TIME_BEFORE_CHANGE = randint(100,250)
        self.speed = randint(2,8)/2
        self.direction = randint(0, 360)
        self.dir_time = self.DIRECTION_TIME_BEFORE_CHANGE
        self.color = consts.FISH_COLOR

        for x in range(int(self.rect.width)):
            for y in range(int(self.rect.height)):
                if self.image.get_at((x,y))[0] != 0:
                    self.image.set_at((x,y), self.color)


    def randomizeDirection(self):
        if self.dir_time <= 0:
            self.dir_time = self.DIRECTION_TIME_BEFORE_CHANGE
            self.direction = randint(0, 360)
            # print("new dir: ", self.direction)
        else:
            self.dir_time-=1
    
    def flipDirection(self):
        self.direction = (self.direction+180)%360
        # print("overlap: ", self.direction)
    
    def update(self):
        self.rect.x += self.speed*math.cos(math.radians(self.direction))
        self.rect.y += self.speed*math.sin(math.radians(self.direction))

        self.randomizeDirection()


