import pygame
from logging import Logger

from mqtt_shared import Topics, ConnectionManager, WordSelectBody
from game_shared import MQTT_DATA_ACTIONS, GAME_MODES, GAME_STATUS, GAME_LEVELS

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

        self._vocabengroup = pygame.sprite.Group()
        self._vocabzhdrawgroup = pygame.sprite.Group()
        self.__all_spritegroups = [self._vocabengroup, self._vocabzhdrawgroup]
        self.__level = self.__mode = None

        self._mask = self._area = None
        self.__setup_mask(True)
        self.__status = GAME_STATUS.HALTED

        self._eventbus.subscribe(Topics.word_select(), lambda x: self.__add_ZH_draw_vocab(x))

    @property 
    def mask(self): 
        return self._mask.to_surface() if self._mask else pygame.Surface((0,0))
        # return pygame.surfarray.make_surface(self._mask) if self._mask else pygame.Surface((0,0))

    @property
    def status(self):
        return self.__status
    
    def __setup_mask(self, is_override = False):
        temp = self._getmask(is_override or not self._mask or self._area is None)
        if temp: self._mask, self._area = temp

    def __init_game(self, level, mode):
        self.__level = level
        self.__mode = mode
        self.__vocab_options = init_vocab_options(self.__level, self.__mode)
        [spg.empty() for spg in self.__all_spritegroups]
        self.__init_new_vocab()
        self.__status=GAME_STATUS.ACTIVE
    
    def __init_new_vocab(self):
        for i in range(consts.VOCAB_AMOUNT):
            ENvocab = MainVocabSprite(self.__vocab_options[i], self._eventbus)
            placement = randomize_vacant_location(ENvocab, self._global_data.window_size, self._mask, self._vocabengroup)
            if (placement):
                self._vocabengroup.add(ENvocab)
            else: ENvocab.kill()

    def __add_ZH_draw_vocab(self, data: WordSelectBody):
        MINIMUM_AREA_FOR_WORD_PRESENTATION = (self._global_data.window_size[0]*self._global_data.window_size[1])/10
        main_vocab = next((sp for sp in self._vocabengroup.sprites() if sp.vocabMain == data.word), None)
        
        if not main_vocab:
            self._logger.error(f"selected word not in bank! selected: {data.selected}; vocab: [{', '.join([sp.vocabMain for sp in self._vocabengroup.sprites()])}]")
            return
        if self._area < MINIMUM_AREA_FOR_WORD_PRESENTATION:
            self._logger.warning(f"not enough space to present word! selected: {data.selected};")
            return
        
        temp = OptionVocabSprite({"word": data.word, "meaning": data.selected}, self._eventbus)
        temp.twin = main_vocab
        placement = randomize_vacant_location(temp, self._global_data.window_size, self._mask)
        while (not placement or temp.distance_to_twin < consts.MIN_DISTANCE_TO_TWIN):
            placement = randomize_vacant_location(temp, self._global_data.window_size, self._mask)

        self._vocabzhdrawgroup.add(temp)

    def __check_collision(self, group):
        for sp in group.sprites():
            if sp.is_out_of_bounds:
                sp.on_collision(sp.area)
                continue
            
            overlap_area = self._mask.overlap_area(sp.mask, (sp.rect.x, sp.rect.y))
            sp.on_collision(overlap_area)

    def __vocab_matching(self): 
        for sp in self._vocabzhdrawgroup.sprites():
            collides = pygame.sprite.collide_mask(sp, sp.twin)
            if collides:
                self._logger.info(f'testing word: {sp.vocabTranslation}/{sp.vocabMain}; left words: {len(self._vocabengroup.sprites())}')
                sp.test_match()
                if len(self._vocabengroup.sprites()) == 0:
                    self._eventbus.publish(Topics.STATE, {"state": self.__finish_game()})

    def __finish_game(self):
        self._logger.info("game finished!")
        self.__status=GAME_STATUS.DONE
        return self.__status

    def start_game(self, payload = None):
        if(len(self._vocabengroup.sprites()) and payload):
            self.__status=GAME_STATUS.ACTIVE
        else:
            if payload and isinstance(payload['level'], GAME_LEVELS) and isinstance(payload['mode'], GAME_MODES):
                self.__init_game(payload['level'].value, payload['mode'].value)
            else:
                self._logger.error(f'invalid start_game payload: {payload}')

    def pause_game(self):
        self.__status=GAME_STATUS.HALTED

    def stop_game(self):
        self.__status=GAME_STATUS.HALTED
        [spg.empty() for spg in self.__all_spritegroups]
    
    def spin_words(self) -> None:
        [[sp.spin_word() for sp in spg.sprites()] for spg in self.__all_spritegroups]

    def __logic_stage(self) -> list:
        self.__setup_mask()

        self.__vocab_matching()

        self.__check_collision(self._vocabzhdrawgroup)
        self.__check_collision(self._vocabengroup)

    def __render_stage(self):
        self._vocabzhdrawgroup.update()
        self._vocabzhdrawgroup.draw(self._window)
        self._vocabengroup.draw(self._window)

    def game_loop(self):
        if self.__status == GAME_STATUS.ACTIVE:
            self.__logic_stage()
            self.__render_stage()
