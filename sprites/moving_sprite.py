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

        self.image.set_alpha(0)
        self.__alpha_change_direction = 1

        self.__deleting = False
        self.__flip_times = [time.time()]
        self.__prev_coverage = 0

        self.__direction = None
        self.__rng = np.random.default_rng() # scale for random() = [-4,4]

        self.__randomize_direction()
    
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
        if area_collision and area_collision >= self.__prev_coverage:
            self.flip_direction()
        self.__prev_coverage = area_collision or 0
        return None
    
    def __test_collision_frequency(self):
        curr = time.time()
        last_item = self.__flip_times.pop()
        if curr - last_item < CHANGE_FREQ_MIN:
            if len(self.__flip_times) > SPRITE_STUCK_THRESH: self.remove_self(REMOVAL_REASON.COVERED)
            else: self.__flip_times.extend((last_item, curr))
        else: self.__flip_times = [curr]

    def flip_direction(self):
        if self.__deleting:
            return

        self.__direction = self.__direction.rotate(180)
        self.__test_collision_frequency()

    def remove_self(self, removal_reason: REMOVAL_REASON):
        self.__deleting=True
        self.__alpha_change_direction = -1
        self.__direction = pygame.math.Vector2(0,0)
    
    def __update_alpha(self):
        if self.__alpha_change_direction != 0:
            curr_alpha = self.image.get_alpha()
            new_val = curr_alpha + self.__alpha_change_direction*SPRITE_APPEAR_SPEED
            print("__update_alpha", curr_alpha, new_val, self.__deleting)
            if new_val >= SPRITE_MAX_OPACITY:
                new_val = SPRITE_MAX_OPACITY
                self.__alpha_change_direction = 0
            elif new_val <= 0:
                new_val = 0
                self.__alpha_change_direction = 0

            self.image.set_alpha(new_val)

            if self.__deleting and new_val == 0:
                if hasattr(self, "on_deleting"): self.on_deleting()
                self.kill()

    def update(self):
        self._floatlocation = [self._floatlocation[i]+self.__direction[i] for i in range(0,2)]
        self.rect.x, self.rect.y = self._floatlocation

        self.__update_alpha()
        self.__randomize_direction()

    def set_location(self, coordinates):
        self._floatlocation = coordinates
        self.rect.x, self.rect.y = self._floatlocation
