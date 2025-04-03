import pygame
from utils.consts import SPRITE_APPEAR_SPEED, BLINK_AMOUNT, BLINK_TIME, SPRITE_MAX_OPACITY

class RemovalAnimator:
    def __init__(self, sprite):
        self._sprite = sprite
        self._is_completed = False

    @property
    def is_completed(self): return self._is_completed

    def update(self):
        raise NotImplementedError("method 'update' not implemented on RemovalAnimator!", self)
    
class FadeOutAnimator(RemovalAnimator):
    def __init__(self, sprite):
        super().__init__(sprite)

    def update(self):
        curr_alpha = self._sprite.image.get_alpha()
        new_alpha = curr_alpha-SPRITE_APPEAR_SPEED
        if new_alpha < 0:
            new_alpha = 0
            self._is_completed = True
        self._sprite.image.set_alpha(new_alpha)

class BlinkAnimator(RemovalAnimator):
    def __init__(self,sprite):
        super().__init__(sprite)
        self.__time_counter = 0
        self.__blink_counter = 0

    def __toggle_alpha(self):
        if self._sprite.image.get_alpha() > SPRITE_MAX_OPACITY / 2:
            self._sprite.image.set_alpha(0)
        else: self._sprite.image.set_alpha(SPRITE_MAX_OPACITY)

    def update(self):
        self.__time_counter+=1
        if self.__time_counter > BLINK_TIME:
            self.__toggle_alpha()
            self.__time_counter = 0
            self.__blink_counter+=1
        if self.__blink_counter > (BLINK_AMOUNT * 2):
            self._is_completed = True

