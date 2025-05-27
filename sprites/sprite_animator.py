import pygame
import math
import random
from utils.consts import *  
from utils.data_singleton import DataSingleton

class SpriteAnimator:
    def __init__(self, sprite):
        self._sprite = sprite
        self._is_completed = False

    @property
    def is_completed(self): return self._is_completed

    def update(self):
        raise NotImplementedError("method 'update' not implemented on SpriteAnimator!", self)
    
class FadeInAnimator(SpriteAnimator):
    def __init__(self, sprite):
        super().__init__(sprite)

    def update(self):
        curr_alpha = self._sprite.image.get_alpha()
        new_alpha = curr_alpha+SPRITE_APPEAR_SPEED
        if new_alpha > SPRITE_MAX_OPACITY:
            new_alpha = SPRITE_MAX_OPACITY
            self._is_completed = True
        self._sprite.image.set_alpha(new_alpha)

class FadeOutAnimator(SpriteAnimator):
    def __init__(self, sprite):
        super().__init__(sprite)

    def update(self):
        curr_alpha = self._sprite.image.get_alpha()
        new_alpha = curr_alpha-SPRITE_APPEAR_SPEED
        if new_alpha < 0:
            new_alpha = 0
            self._is_completed = True
        self._sprite.image.set_alpha(new_alpha)

class BlinkAnimator(SpriteAnimator):
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

class FireworksParticle(pygame.sprite.Sprite):
    def __init__(self, color, coords, dist, win_h):
        super().__init__()
        self.__color = color
        self.image = pygame.Surface((FIREWORKS_PARTICLE_SIZE*2, FIREWORKS_PARTICLE_SIZE*2))
        pygame.draw.circle(self.image, self.__color, (FIREWORKS_PARTICLE_SIZE, FIREWORKS_PARTICLE_SIZE), FIREWORKS_PARTICLE_SIZE)
        self.image.set_alpha(250)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = coords

        self.__dx, self.__dy = dist
        self.__win_height = win_h

    def update(self):
        self.rect.x += self.__dx
        self.rect.y += self.__dy
        self.__dy+=FIREWORK_SPEED

        curr_alpha = self.image.get_alpha()
        self.image.set_alpha(curr_alpha - FIREWORK_DISAPPEAR_SPEED)

        if curr_alpha < 10 or self.rect.y > self.__win_height:
            self.kill()

class FireworksAnimator(SpriteAnimator):
    def __init__(self, sprite, center = None):
        super().__init__(sprite)
        self.__particles = pygame.sprite.Group()
        self.__center = center if center else self._sprite.sprite_midpoint
        self.__global_data = DataSingleton()

        for i in range(FIREWORKS_PARTICLE_AMOUNT):
            direction = random.random() * math.pi * 2
            velocity = random.random() * SPRITE_MAX_SPEED
            self.__particles.add(FireworksParticle(
                self._sprite._get_color, self.__center,
                (math.cos(direction) * velocity, math.sin(direction) * velocity),
                self.__global_data.window_size[1]
            ))

    def __get_fireworks_alpha(self):
        res = None
        if len(self.__particles.sprites()):
            res= self.__particles.sprites()[0].image.get_alpha()
        return res

    def update(self):
        self.__particles.update()
        self.__particles.draw(self.__global_data.window)
        self._sprite.image.set_alpha(self.__get_fireworks_alpha())
        self._sprite.twin.image.set_alpha(self.__get_fireworks_alpha())
        if len(self.__particles.sprites()) == 0:
            self._is_completed = True
