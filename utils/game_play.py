import pygame
from logging import Logger
from random import sample
import time

from mqtt_shared import Topics
from game_shared import MQTT_DATA_ACTIONS, GAME_MODES, GAME_STATUS, GAME_LEVELS, VocabItem

from .event_bus import EventBus
from .data_singleton import DataSingleton
import utils.consts as consts
from utils.helper_functions import init_vocab_options, is_pygame_pt_in_contour, calc_contour_midpoint
from sprites import MainVocabSprite, OptionVocabSprite

class DelayedAction ():
    def __init__(self, callback: callable, params: list = None, timer: int = consts.WAIT_AFTER_MATCH):
        self.__is_done = False
        self.__counter = timer
        self.__callback = callback
        self.__params = params if params and isinstance(params, list) else []
    @property
    def is_done(self): return self.__is_done
    def countdown (self):
        self.__counter-=1
        if self.__counter == 0:
            self.__callback(*self.__params)
            self.__is_done = True

class GamePlay():
    def __init__(self, eventbus: EventBus, getMask: callable):

        self._global_data = DataSingleton()

        self._getmask = getMask
        self._eventbus = eventbus
        self.__vocab_options = []

        self.__vocab_sprites = pygame.sprite.Group()
        self.__level = self.__mode = None
        self.__new_word_stage = True

        self._contours_info = []
        self._mask = None
        self.__setup_mask(True)
        self.__status = GAME_STATUS.HALTED

        self.__delayed_actions = []

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
        if temp:
            old_contours_amount = len(self._contours_info)
            self._mask, self._contours_info = temp
            if old_contours_amount != len(self._contours_info):
                self._eventbus.publish(Topics.CONTOURS, {"contours": len(self._contours_info)})
                if len(self._contours_info)==0 and len(self.__vocab_sprites.sprites()) == 0:
                    self.__new_word_stage = True

    def __init_game(self, level, mode):
        self.__level = level
        self.__mode = mode
        self.__new_word_stage = True
        self.__remove_all_vocab()
        self.__vocab_options = init_vocab_options(self.__level, self.__mode)
        self.__status=GAME_STATUS.ACTIVE

    def __add_EN_vocab(self):
        if len(self.__vocab_sprites.sprites()) < consts.MAX_VOCAB_ACTIVE:
            relevant_cnt = self._contours_info[0] if len(self._contours_info) else None
            if relevant_cnt:
                unsolved = self.__get_unsolved_vocab()
                if (unsolved):
                    word = sample(unsolved, 1)[0]
                    ENvocab = MainVocabSprite(word, self._eventbus)
                    ENvocab.set_location(calc_contour_midpoint(relevant_cnt["contour"]))
                    self.__vocab_sprites.add(ENvocab)
                    self.__new_word_stage = False

    def __add_ZH_draw_vocab(self, data: dict):
        word = data["word"] if isinstance(data, dict) else data.word
        selected = data["selected"] if isinstance(data, dict) else data.selected
        main_vocab = next((sp for sp in self.__vocab_sprites.sprites() if isinstance(sp, MainVocabSprite) and sp.vocabMain == word), None)

        if not main_vocab:
            self._global_data.logger.error(f"selected word not currently presented! word:{word}; selected: {selected}")
            # self._eventbus.publish(Topics.word_state(), {"type": MQTT_DATA_ACTIONS.SELECT_FAIL, "word": main_vocab.as_dict()}) # publish remove instead???
            return
        
        destenation_contour = next((cnt for cnt in self._contours_info
                                    if not is_pygame_pt_in_contour(cnt["contour"], main_vocab.sprite_midpoint)), None)
        if not destenation_contour:
            self._eventbus.publish(Topics.word_state(), {"type": MQTT_DATA_ACTIONS.SELECT_FAIL, "word": main_vocab.as_dict()})
            self._global_data.logger.warning(f"not enough contours to present word! selected: {selected};")
            return
        
        temp = OptionVocabSprite(VocabItem(word= word, meaning= selected), self._eventbus)
        temp.twin = main_vocab
        temp.set_location(calc_contour_midpoint(destenation_contour["contour"]))
        self.__vocab_sprites.add(temp)

    def __check_collision(self):
        for sp in self.__vocab_sprites.sprites():
            if not sp.is_deleting:
                if sp.is_out_of_bounds:
                    sp.on_collision(sp.area)
                    continue
                
                overlap_area = self._mask.overlap_area(sp.mask, (sp.rect.x, sp.rect.y))
                sp.on_collision(overlap_area)

    def __vocab_matching(self): 
        for sp in [sp for sp in self.__vocab_sprites.sprites() if isinstance(sp, OptionVocabSprite) and not sp.is_deleting]:
            collides = pygame.sprite.collide_mask(sp, sp.twin)
            if collides:
                self._global_data.logger.info(f'testing word: {sp.vocabTranslation}/{sp.vocabMain}')
                sp.test_match()
                unsolved = self.__get_unsolved_vocab()
                if not unsolved:
                    self.__delayed_actions.append(DelayedAction(self.__finish_game))

    def __finish_game(self):
        self._global_data.logger.info("game finished!")
        self.__status=GAME_STATUS.DONE
        self._eventbus.publish(Topics.STATE, {"state": GAME_STATUS.DONE})
        return self.__status

    def start_game(self, payload = None):
        if len(self.__get_unsolved_vocab()):
            self.__status=GAME_STATUS.ACTIVE
            self._eventbus.publish(Topics.STATE, {"state": GAME_STATUS.ACTIVE})
        else:
            if payload and isinstance(payload['level'], GAME_LEVELS) and isinstance(payload['mode'], GAME_MODES):
                self.__init_game(payload['level'].value, payload['mode'].value)
                self._eventbus.publish(Topics.STATE, {"state": GAME_STATUS.ACTIVE})
            else:
                self._global_data.logger.error(f'invalid start_game payload: {payload}')

    def pause_game(self):
        self.__status=GAME_STATUS.HALTED
        self._eventbus.publish(Topics.STATE, {"state": GAME_STATUS.HALTED})

    def stop_game(self):
        self.__remove_all_vocab()
        self.__status=GAME_STATUS.STOPPED
        self._eventbus.publish(Topics.STATE, {"state": GAME_STATUS.STOPPED})
    
    def __remove_all_vocab(self):
        self.__vocab_sprites.empty()
        self.__vocab_options = []

    def spin_words(self) -> None:
        [sp.spin_word() for sp in self.__vocab_sprites.sprites()]

    def __logic_stage(self) -> list:
        self.__setup_mask()

        self.__vocab_matching()
        self.__check_collision()

        if self.__new_word_stage:
            self.__add_EN_vocab()

    def __render_stage(self):
        # for ct in self._contours_info:
        #     pygame.draw.polygon(self._window, (100, 100, 100), convert_contour_to_polygon(ct["contour"]), 5)
        self.__vocab_sprites.update()
        self.__vocab_sprites.draw(self._global_data.window)

    def __handle_delayed(self):
        indexes_to_del = []
        for (i, ac) in enumerate(self.__delayed_actions):
            ac.countdown()
            if ac.is_done:
                indexes_to_del.append(i)
        [self.__delayed_actions.pop(i) for i in indexes_to_del[::-1]]

    def game_loop(self):
        if self.__status == GAME_STATUS.ACTIVE:
            self.__logic_stage()
            self.__render_stage()
            self.__handle_delayed()
            