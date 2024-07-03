import pygame
import utils.consts as consts
import numpy as np
from random import randint
import math

class Contour(pygame.sprite.Sprite):
    def __init__(self, img, bounding, color):
        super().__init__()
        self.color = color
        self.setShape(img, bounding)
        self.internal_sprites = pygame.sprite.Group()
        self.internal_sprites.add(self.newInternalSprite())

    def updateShape(self, img, bounding):
        self.setShape(img, bounding)
        #TODO: change sprite location/rempove it and add new?
        return self
    
    def newInternalSprite(self):
        sprite = InternalSprite(consts.FISH_SIZE)
        sprite.rect.x, sprite.rect.y = self.randomizeInternalLocation(sprite)

        return sprite

    def setShape(self, img, bounding):
        parent_image = (pygame.transform.flip(pygame.surfarray.make_surface(np.rot90(img)), True, False)).subsurface(bounding)
        self.mask = pygame.mask.from_threshold(parent_image, self.color, threshold=(1, 1, 1))
        self.image = self.mask.to_surface()
        self.image.set_colorkey((0,0,0))
        self.rect = self.image.get_rect()
        # self_opmask = self.mask
        pygame.mask.Mask.invert(self.mask)
        self.opmask_surf = self.mask.to_surface()

        # color the contours
        for x in range(int(bounding[consts.BOUND_LEGEND["WIDTH"]])):
            for y in range(int(bounding[consts.BOUND_LEGEND["HEIGHT"]])):
                if self.image.get_at((x,y))[0] != 0:
                    self.image.set_at((x,y),self.color)
        
        self.rect.x = bounding[consts.BOUND_LEGEND["X"]]
        self.rect.y = bounding[consts.BOUND_LEGEND["Y"]]
        self.rect.height = bounding[consts.BOUND_LEGEND["HEIGHT"]]
        self.rect.width = bounding[consts.BOUND_LEGEND["WIDTH"]]

    def randomizeInternalLocation(self, sprite):
        def random_location():
            random_x = randint(0, int(math.floor(self.rect.width - sprite.rect.height)))
            random_y = randint(0, int(math.floor(self.rect.height - sprite.rect.width)))
            return (random_x, random_y)
        #TODO: check range and if not ok then don't add parent sprite!@!!!!1

        x,y = random_location()

        # while self.mask.overlap(sprite.mask, (x, y)):
        # # while self.opmask_surf.get_at((x,y))[0] != 0:
            # x,y = random_location()

        return (x,y)

    def update(self):
        if pygame.mouse.get_pos():
            
            for sp in self.internal_sprites:
                dot = self.mask.overlap(sp.mask, (sp.rect.x, sp.rect.y))
                if dot:
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


