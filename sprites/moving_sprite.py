import pygame
from utils import DataSingleton
from utils.consts import *
import time
from random import randint, uniform

from .sprite_animator import FadeInAnimator, FadeOutAnimator, BlinkAnimator, FireworksAnimator

class MovingSprite(pygame.sprite.Sprite):
    def __init__(self, img):
        super().__init__()
        self._global_data = self._global_data if hasattr(self, "_global_data") else DataSingleton()

        self.image = img
        self.rect = self.image.get_rect()

        self._floatlocation = (0.,0.)

        self.image.set_alpha(0)
        self.__deleting = False
        self.__sprite_animator = FadeInAnimator(self)

        self.__flip_times = [time.time()]
        self.__prev_coverage = 0
        self.__coverage_unchanged_frames = 0

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
        if area_collision and area_collision > self.__prev_coverage:
            self.flip_direction()
        self.__test_coverage_movement(area_collision)
        self.__prev_coverage = area_collision or 0
        return None
    
    def __test_coverage_movement(self, area_collision):
        if area_collision > self.rect.height * self.rect.width * SPRITE_MAX_COVERED:
            if self.__prev_coverage * (1-SPRITE_MAX_COVERED) <= area_collision:
                self.__coverage_unchanged_frames+=1
            if self.__coverage_unchanged_frames > SPRITE_COVERED_FRAMES_BEFORE_DEL:
                self.remove_self(REMOVAL_REASON.COVERED)
        else:
            self.__coverage_unchanged_frames = 0

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
        # self.__test_collision_frequency()

    def __get_twin_collision_center(self):
        left  = max( self.rect.left,  self.twin.rect.left )
        right = min( self.rect.right, self.twin.rect.right )
        top   = max( self.rect.top,   self.twin.rect.top )
        bottom= min( self.rect.bottom, self.twin.rect.bottom )
        return (int((right+left)/2), int((top+bottom)/2))

    def remove_self(self, removal_reason: REMOVAL_REASON):
        self.__deleting = True
        if hasattr(self, "on_deleting"): self.on_deleting()
        self.__direction = pygame.math.Vector2(0,0)
        match removal_reason.value:
            case REMOVAL_REASON.COVERED.value:
                self.__sprite_animator = FadeOutAnimator(self)
            case REMOVAL_REASON.MATCH_FAIL.value:
                self.__sprite_animator = BlinkAnimator(self)
            case REMOVAL_REASON.MATCH_SUCCESS.value:
                self.__sprite_animator  = FireworksAnimator(self, center=self.__get_twin_collision_center())
            case _:
                self.kill()
    
    def update(self):
        self._floatlocation = [self._floatlocation[i]+self.__direction[i] for i in range(0,2)]
        self.rect.x, self.rect.y = self._floatlocation

        self.__randomize_direction()

        if self.__sprite_animator:
            self.__sprite_animator.update()
            if self.__sprite_animator.is_completed:
                self.__sprite_animator = None
                if self.__deleting:
                    self.kill()

    def set_location(self, coordinates: tuple):
        temp_x, temp_y = coordinates
        self._floatlocation = (temp_x - (self.rect.width / 2), temp_y - (self.rect.height / 2))
        self.rect.x, self.rect.y = self._floatlocation
