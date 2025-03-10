import pygame
from utils.consts import *
from utils.dataSingleton import DataSingleton

class GenVocabSprite(pygame.sprite.Sprite):
    def __init__(self, vocab_i, property):
        super().__init__()

        self._language = property
        self._global_data = DataSingleton()
        self._vocab = self._global_data.vocab_options[vocab_i]
        self._color = (0,0,255) if property == "en" else (255,0,0)
        self._floatlocation = (0.,0.)
        self._twin = None

        self.image = self._global_data.vocab_font.render(self._vocab[self._language], True, self._color)
        self.spin_word()
        self.rect = self.image.get_rect()

        self.mask = pygame.mask.from_surface(self.image)
        pygame.mask.Mask.invert(self.mask)
        self.area = self.mask.count()

        # color = (255,0,0)
        # for x in range(int(self.rect.width)):
        #     for y in range(int(self.rect.height)):
        #         if self.mask.get_at((x,y)) != 0:
        #             self.image.set_at((x,y), color)
            
    @property
    def vocabEN(self): return self._vocab["en"]
    @property
    def vocabZH(self): return self._vocab["zh"]
    @property
    def is_out_of_bounds(self): return any([self._floatlocation[i] < 0 or self._floatlocation[i] + self.rect[2+i] > self._global_data.window_size[i] for i in range(0,2)])
    @property
    def as_dict(self): return {"en": self._vocab["en"], "zh": self._vocab["zh"]}
    @property
    def twin(self): return self._twin
    @twin.setter
    def twin(self, sprite):
        self._twin = sprite
        if self._twin.twin is None: self._twin._twin = self
    @property
    def sprite_midpoint(self): return (self.rect.x + self.rect.width/2, self.rect.y + self.rect.height/2)
    @property
    def distance_to_twin(self): return pygame.math.Vector2(self.sprite_midpoint).distance_to(self.twin.sprite_midpoint)


    def match_success(self):
        if self._twin: self._twin.kill()
        self.kill()

    def set_location(self, coordinates):
        self._floatlocation = coordinates
        self.rect.x, self.rect.y = self._floatlocation

    def on_collision(self, area: int):
        raise NotImplementedError("method not implemented")
    
    def spin_word(self):
        self.image = self._global_data.vocab_font.render(self._vocab[self._language], True, self._color)
        self.image = pygame.transform.flip(self.image, not self._global_data.is_spin, self._global_data.is_spin)

