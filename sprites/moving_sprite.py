import pygame
from game_shared import VocabItem
from utils import DataSingleton, EventBus
from utils.consts import *
import time
from random import randint, uniform

class MovingSprite(pygame.sprite.Sprite):
    def __init__(self, img):
        super().__init__()
        self._global_data = self._global_data if hasattr(self, "_global_data") else DataSingleton()

        self.image = img
        self.rect = self.image.get_rect()

        self._floatlocation = (0.,0.)

        self.__appearing = 0.0
        self.__deleting = False
        self.__flip_times = [time.time()]

        self.__direction = None
        self.__rng = np.random.default_rng() # scale for random() = [-4,4]

        self.__randomize_direction()
        self.__set_alpha()
    
    @property
    def is_out_of_bounds(self): return any([self._floatlocation[i] < 0 or self._floatlocation[i] + self.rect[2+i] > self._global_data.window_size[i] for i in range(0,2)])
    @property
    def sprite_midpoint(self): return (self.rect.x + self.rect.width/2, self.rect.y + self.rect.height/2)
    @property
    def is_deleting(self): return self.__deleting

    def __randomize_direction(self):
        if self.__deleting:
            return
        else:
            self.__direction = self.__randomize_angle()

    def __randomize_sign(self): return -1 if randint(0,1) else 1

    def __randomize_angle(self):
        res=None
        if self.__direction:
            change_course = self.__rng.normal()
            res = self.__direction.rotate(change_course*(SPRITE_ANGLE_MAX_DIFF/4)) if change_course > 0.5 else self.__direction
            if res.length() < 1: res.normalize()*uniform(SPRITE_MIN_SPEED,SPRITE_MAX_SPEED)
        else: res = pygame.math.Vector2(self.__randomize_sign()*uniform(SPRITE_MIN_SPEED, SPRITE_MAX_SPEED), self.__randomize_sign()*uniform(SPRITE_MIN_SPEED, SPRITE_MAX_SPEED))
        return res

    def on_collision(self, area_collision: int) -> None:
        if area_collision: self.flip_direction()
        return None
    
    def flip_direction(self):
        if self.__deleting:
            return

        self.__direction = self.__direction.rotate(180)

        last_item = self.__flip_times.pop()
        curr = time.time()
        if curr - last_item < 1: [self.remove_self(True) if len(self.__flip_times) > SPRITE_STUCK_THRESH else self.__flip_times.extend((last_item, curr))]
        else:
            self.__flip_times = [curr]
        
    def remove_self(self, is_collision = False):
        self.__deleting=True
        if is_collision: self.__direction = pygame.math.Vector2(0,0)
    
    def __set_alpha(self):
        self.image.set_alpha(self.__appearing*SPRITE_MAX_OPACITY)
        if (self.__deleting):
            self.__appearing -=SPRITE_APPEAR_SPEED
            if self.__appearing <= 0.0:
                if hasattr(self, "on_deleting"): self.on_deleting()
                self.__deleting = False
                self.kill()
        elif (self.__appearing < 1.0): self.__appearing = 1.0 if self.__appearing+SPRITE_APPEAR_SPEED > 1.0 else self.__appearing+SPRITE_APPEAR_SPEED

    def update(self):
        self._floatlocation = [self._floatlocation[i]+self.__direction[i] for i in range(0,2)]
        self.rect.x, self.rect.y = self._floatlocation

        self.__set_alpha()
        self.__randomize_direction()

    def set_location(self, coordinates):
        self._floatlocation = coordinates
        self.rect.x, self.rect.y = self._floatlocation
