import pygame
from random import randint
import math
import utils.consts as consts

#TODO: add addition/disappearance animation
class InternalSprite(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        size = consts.FISH_SIZE
        image = pygame.image.load(consts.INTERNAL_SPRITE_IMG).convert_alpha()
        image = pygame.transform.scale(image, size)
        self.image = pygame.Surface((size[0] + consts.FISH_BORDER*2, size[1] + consts.FISH_BORDER*2), pygame.SRCALPHA)
        self.image.blit(image, (consts.FISH_BORDER, consts.FISH_BORDER))
        
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)

        self.DIRECTION_TIME_BEFORE_CHANGE = randint(100,250)
        self.speed = randint(2,8)/2
        self.direction = randint(0, 360)
        self.dir_time = self.DIRECTION_TIME_BEFORE_CHANGE
        self.color = consts.FISH_COLOR

        for x in range(int(self.rect.width)):
            for y in range(int(self.rect.height)):
                if self.mask.get_at((x,y)) != 0:
                    self.image.set_at((x,y), self.color)

        pygame.mask.Mask.invert(self.mask)
        self.area = self.mask.count()
        
    def randomizeDirection(self):
        if self.dir_time <= 0:
            self.dir_time = self.DIRECTION_TIME_BEFORE_CHANGE
            self.direction = randint(0, 360)
        else:
            self.dir_time-=1
    
    def flipDirection(self):
        self.direction = (self.direction+180)%360
    
    def update(self):
        self.rect.x += self.speed*math.cos(math.radians(self.direction))
        self.rect.y += self.speed*math.sin(math.radians(self.direction))

        self.randomizeDirection()

