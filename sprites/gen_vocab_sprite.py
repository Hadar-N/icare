import pygame
from game_shared import VocabItem
from utils import DataSingleton, EventBus
from utils.consts import *

class GenVocabSprite(pygame.sprite.Sprite):
    def __init__(self, vocab: VocabItem, eventbus: EventBus):
        super().__init__()

        self._global_data = DataSingleton()
        self._vocab = vocab
        self._color = self._get_color
        self._floatlocation = (0.,0.)
        self._twin = None

        self.image = self._global_data.vocab_font.render(self.vocabSelf, True, self._color)
        self.spin_word()
        self.rect = self.image.get_rect()

        self.mask = pygame.mask.from_surface(self.image)
        pygame.mask.Mask.invert(self.mask)
        self.area = self.mask.count()

        self._eventbus = eventbus

        # color = (255,0,0)
        # for x in range(int(self.rect.width)):
        #     for y in range(int(self.rect.height)):
        #         if self.mask.get_at((x,y)) != 0:
        #             self.image.set_at((x,y), color)
    
    @property
    def vocabMain(self): return self._vocab.word
    @property
    def vocabTranslation(self): return self._vocab.meaning

    @property
    def vocabSelf(self): raise NotImplementedError("method 'vocabSelf' not implemented!", self)
    @property
    def _get_color(self): raise NotImplementedError("method '_get_color' not implemented!", self)

    @property
    def twin(self): return self._twin
    @twin.setter
    def twin(self, sprite):
        self._twin = sprite
        if self._twin and not self._twin.twin: self._twin.twin = self

    @property
    def is_out_of_bounds(self): return any([self._floatlocation[i] < 0 or self._floatlocation[i] + self.rect[2+i] > self._global_data.window_size[i] for i in range(0,2)])
    @property
    def sprite_midpoint(self): return (self.rect.x + self.rect.width/2, self.rect.y + self.rect.height/2)
    @property
    def distance_to_twin(self): return pygame.math.Vector2(self.sprite_midpoint).distance_to(self.twin.sprite_midpoint)

    def as_dict(self, removed_args:list[str] = []): return self._vocab.asDict(removed_args)

    def match_success(self):
        if self._twin: 
            self._twin._vocab.is_solved = True
            self._twin.kill()
        self._vocab.is_solved = True
        self.kill()

    def set_location(self, coordinates):
        self._floatlocation = coordinates
        self.rect.x, self.rect.y = self._floatlocation

    def on_collision(self, area: int):
        raise NotImplementedError("method not implemented")
    
    def spin_word(self):
        self.image = self._global_data.vocab_font.render(self.vocabSelf, True, self._color)
        self.image = pygame.transform.flip(self.image, not self._global_data.is_spin, self._global_data.is_spin)

