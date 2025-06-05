from io import BytesIO
import pygame
import cairosvg

from .moving_sprite import MovingSprite
from game_shared import VocabItem
from utils import DataSingleton, EventBus
from utils.consts import *

class GenVocabSprite(MovingSprite):
    def __init__(self, vocab: VocabItem, eventbus: EventBus, is_speaker = False):
        self._global_data = DataSingleton()

        self._vocab = vocab
        self._is_speaker = is_speaker
        self._color = self._get_color
        
        super().__init__(self.spin_word())

        self.mask = pygame.mask.from_surface(self.image)
        pygame.mask.Mask.invert(self.mask)
        self.area = self.mask.count()

        self._twin = None
        self._eventbus = eventbus

        # color = (255,0,0)
        # for x in range(int(self.rect.width)):
        #     for y in range(int(self.rect.height)):
        #         if self.mask.get_at((x,y)) != 0:
        #             self.image.set_at((x,y), color)
    
    @property
    def vocabMain(self) -> str: return self._vocab.word
    @property
    def vocabTranslation(self) -> str: return self._vocab.meaning

    @property
    def vocabSelf(self) -> str: raise NotImplementedError("method 'vocabSelf' not implemented!", self)
    @property
    def _get_color(self) -> tuple: raise NotImplementedError("method '_get_color' not implemented!", self)

    @property
    def twin(self): return self._twin
    @twin.setter
    def twin(self, sprite):
        self._twin = sprite
        if self._twin and not self._twin.twin: self._twin.twin = self

    @property
    def distance_to_twin(self): return pygame.math.Vector2(self.sprite_midpoint).distance_to(self.twin.sprite_midpoint)

    def as_dict(self, removed_args:list[str] = []): return self._vocab.asDict(removed_args)

    def match_success(self):
        if self._twin: 
            self._twin._vocab.is_solved = True
            self._twin.remove_self(REMOVAL_REASON.MATCH_SUCCESS)
        self._vocab.is_solved = True
        self.remove_self(REMOVAL_REASON.MATCH_SUCCESS)
    
    def __create_text(self):
        res = self._global_data.vocab_font.render(self.vocabSelf, True, self._color)
        res = pygame.transform.flip(res, not self._global_data.is_spin, self._global_data.is_spin)
        return res
    def __create_img(self):
        with open(SPEAKER_PATH, 'r') as f:
            svg_content = f.read()
        svg_content = svg_content.replace('fill="#231F20"', f'fill="rgb({",".join([str(i) for i in self._get_color])})"')
        png_data = cairosvg.svg2png(bytestring=svg_content.encode(),  output_width=FONT_SIZE*1.5, output_height=FONT_SIZE*1.2)
        return pygame.image.load(BytesIO(png_data))

    def spin_word(self):
        res = self.__create_img() if self._is_speaker else self.__create_text()
        if hasattr(self, "image"):
            print(hasattr(self, "image"), self.image)
            self.image = res
        return res


