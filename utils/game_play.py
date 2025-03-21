import pygame
from logging import Logger
from random import sample
import numpy as np

from mqtt_shared import Topics, ConnectionManager, WordSelectBody
from game_shared import MQTT_DATA_ACTIONS, GAME_MODES, GAME_STATUS, GAME_LEVELS, VocabItem

from .event_bus import EventBus
from .data_singleton import DataSingleton
import utils.consts as consts
from utils.helper_functions import init_vocab_options, randomize_vacant_location, isVarInEnum
from sprites import MainVocabSprite, OptionVocabSprite

class GamePlay():
    def __init__(self, window: pygame.Surface, logger: Logger, eventbus: EventBus, getMask):

        self._global_data = DataSingleton()
        self._logger = logger
        self._window = window

        self._getmask = getMask
        self._eventbus = eventbus
        self.__vocab_options = []

        self.__vocab_sprites = pygame.sprite.Group()
        self.__level = self.__mode = None

        self._contours_info = []
        self._mask = None
        self.__setup_mask(True)
        self.__status = GAME_STATUS.HALTED
        self.MINIMUM_AREA_FOR_WORD_PRESENTATION = (self._global_data.window_size[0]*self._global_data.window_size[1])/consts.MIN_FRAME_CONTENT_PARTITION

        self._eventbus.subscribe(Topics.word_select(), lambda x: self.__add_ZH_draw_vocab(x))

    @property 
    def mask(self): 
        return self._mask.to_surface() if self._mask else pygame.Surface((0,0))
        # return pygame.surfarray.make_surface(self._mask) if self._mask else pygame.Surface((0,0))

    @property
    def status(self):
        return self.__status
    
    def __get_unsolved_vocab(self): return [v for v in self.__vocab_options if not v.is_solved]

    def __setup_mask(self, is_override = False):
        temp = self._getmask(is_override or not self._mask or not len(self._contours_info))
        if temp: self._mask, self._contours_info = temp

    def __init_game(self, level, mode):
        self.__level = level
        self.__mode = mode
        self.__vocab_options = [VocabItem(**item) for item in init_vocab_options(self.__level, self.__mode)]
        self.__vocab_sprites.empty()
        self.__status=GAME_STATUS.ACTIVE

    def __add_EN_vocab(self):
        if len(self.__vocab_sprites.sprites()) < consts.MAX_VOCAB_ACTIVE:
            relevant_cnt = next((cnt for cnt in self._contours_info if cnt["area"] > self.MINIMUM_AREA_FOR_WORD_PRESENTATION), None)
            if relevant_cnt:
                unsolved = self.__get_unsolved_vocab()
                if (unsolved):
                    word = sample(unsolved, 1)[0]
                    ENvocab = MainVocabSprite(word, self._eventbus)
                    ENvocab.set_location(relevant_cnt["center_pt"])
                    self.__vocab_sprites.add(ENvocab)

    def __add_ZH_draw_vocab(self, data: dict):
        word = data["word"] if isinstance(data, dict) else data.word
        selected = data["selected"] if isinstance(data, dict) else data.selected
        main_vocab = next((sp for sp in self.__vocab_sprites.sprites() if isinstance(sp, MainVocabSprite) and sp.vocabMain == word), None)
        
        if not main_vocab:
            self._logger.error(f"selected word not currently presented! word:{word}; selected: {selected}")
            return
        if np.sum([i["area"] for i in self._contours_info]) < self.MINIMUM_AREA_FOR_WORD_PRESENTATION:
            self._eventbus.publish(Topics.word_state(), {"type": MQTT_DATA_ACTIONS.SELECT_FAIL, "word": main_vocab.as_dict()})
            self._logger.warning(f"not enough space to present word! selected: {selected};")
            return
        
        temp = OptionVocabSprite(VocabItem(word= word, meaning= selected), self._eventbus)
        temp.twin = main_vocab
        placement = randomize_vacant_location(temp, self._global_data.window_size, self._mask)
        while (not placement or temp.distance_to_twin < (consts.MIN_DISTANCE_TO_TWIN * temp.twin.rect.width)):
            placement = randomize_vacant_location(temp, self._global_data.window_size, self._mask)

        self.__vocab_sprites.add(temp)

    def __check_collision(self, group):
        for sp in group.sprites():
            if sp.is_out_of_bounds:
                sp.on_collision(sp.area)
                continue
            
            overlap_area = self._mask.overlap_area(sp.mask, (sp.rect.x, sp.rect.y))
            sp.on_collision(overlap_area)

    def __vocab_matching(self): 
        for sp in [sp for sp in self.__vocab_sprites.sprites() if isinstance(sp, OptionVocabSprite)]:
            collides = pygame.sprite.collide_mask(sp, sp.twin)
            if collides:
                self._logger.info(f'testing word: {sp.vocabTranslation}/{sp.vocabMain}')
                sp.test_match()
                next_word= next((i.word for i in self.__vocab_options if not i.is_solved), None)
                if not next_word:
                    self.__finish_game()

    def __finish_game(self):
        self._logger.info("game finished!")
        self.__status=GAME_STATUS.DONE
        self._eventbus.publish(Topics.STATE, {"state": GAME_STATUS.DONE})
        return self.__status

    def start_game(self, payload = None):
        if(len(self.__vocab_sprites.sprites())):
            self.__status=GAME_STATUS.ACTIVE
            self._eventbus.publish(Topics.STATE, {"state": GAME_STATUS.ACTIVE})
        else:
            if payload and isinstance(payload['level'], GAME_LEVELS) and isinstance(payload['mode'], GAME_MODES):
                self.__init_game(payload['level'].value, payload['mode'].value)
                self._eventbus.publish(Topics.STATE, {"state": GAME_STATUS.ACTIVE})
            else:
                self._logger.error(f'invalid start_game payload: {payload}')

    def pause_game(self):
        self.__status=GAME_STATUS.HALTED
        self._eventbus.publish(Topics.STATE, {"state": GAME_STATUS.HALTED})

    def stop_game(self):
        self.__vocab_sprites.empty()
        self.__status=GAME_STATUS.STOPPED
        self._eventbus.publish(Topics.STATE, {"state": GAME_STATUS.STOPPED})
    
    def spin_words(self) -> None:
        [sp.spin_word() for sp in self.__vocab_sprites.sprites()]

    def __logic_stage(self) -> list:
        self.__setup_mask()

        self.__vocab_matching()
        self.__check_collision(self.__vocab_sprites)

        self.__add_EN_vocab()

    def __render_stage(self):
        self.__vocab_sprites.update()
        self.__vocab_sprites.draw(self._window)

    def game_loop(self):
        if self.__status == GAME_STATUS.ACTIVE:
            self.__logic_stage()
            self.__render_stage()