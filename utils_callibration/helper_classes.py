import pygame
from math import dist

from utils import DataSingleton
from utils.consts import BOUNDARY_RADIUS

global_data = DataSingleton()

class BtnItem():
    def __init__(self, txt, item_no, font, callback):
        self.__rect = pygame.Rect(global_data.full_display_size[0]/2 - 50, global_data.full_display_size[1]/2 + item_no*50, 100, 50)
        self.__color = (200,200,200)
        self.__content = txt
        self.__text_obj = font.render(txt, True, (0,0,0))
        self.__callback = callback

    @property
    def content(self): return self.__content
    @property
    def callback(self): return self.__callback

    def draw_btn(self, screen):
        pygame.draw.rect(screen, self.__color, self.__rect)
        screen.blit(self.__text_obj, (self.__rect[0], self.__rect[1]))

    def is_colliding(self, pos):
        x_colliding = pos[0] > self.__rect[0] and pos[0] < self.__rect[0] + self.__rect[2]
        y_colliding = pos[1] > self.__rect[1] and pos[1] < self.__rect[1] + self.__rect[3]
        return x_colliding and y_colliding

class Boundary(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.__center_point = pos
        self.image = pygame.Surface(global_data.full_display_size, flags=pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255,0,0), pos, BOUNDARY_RADIUS)
        self.rect = self.image.get_rect()

    @property
    def center_point(self): return self.__center_point

    def is_colliding(self, pos):
        return dist(self.__center_point, pos) <= BOUNDARY_RADIUS