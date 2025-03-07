import pygame
from logging import Logger

import utils.consts as consts
from utils.eventBus import EventBus
from utils.dataSingleton import DataSingleton
from utils.helper_functions.game_helpers import init_vocab_options, randomize_vacant_location
from sprites.VocabENSprite import VocabENSprite
from sprites.VocabZHSprite import VocabZHSprite

class GamePlay():
    def __init__(self, window: pygame.Surface, logger: Logger, eventbus: EventBus, getMask):

        self._global_data = DataSingleton()
        self._logger = logger
        self._window = window

        self._getmask = getMask
        self._eventbus = eventbus

        self._vocabengroup = pygame.sprite.Group()
        self._vocabzhbankgroup = pygame.sprite.Group()
        self._vocabzhdrawgroup = pygame.sprite.Group()
        self.__all_spritegroups = [self._vocabengroup, self._vocabzhbankgroup, self._vocabzhdrawgroup]

        self._mask = self._area = None
        self.__setup_mask(True)
        self.__status = consts.GAME_STATUS.HALTED

    @property 
    def mask(self): 
        return self._mask.to_surface() if self._mask else pygame.Surface((0,0))
        # return pygame.surfarray.make_surface(self._mask) if self._mask else pygame.Surface((0,0))

    @property
    def status(self):
        return self.__status

    def __setup_mask(self, isOverride = False):
        temp = self._getmask(isOverride or not self._mask or self._area is None)
        if temp: self._mask, self._area = temp

    def __init_game(self):
        init_vocab_options(self._global_data)
        [spg.empty() for spg in self.__all_spritegroups]
        self.__init_new_vocab()
        self.__status=consts.GAME_STATUS.ACTIVE
    
    def __init_new_vocab(self):
        for i in range(consts.VOCAB_AMOUNT):
            ENvocab = VocabENSprite(i)
            placement = randomize_vacant_location(ENvocab, self._global_data.window_size, self._mask, self._vocabengroup)
            if (placement):
                ZHvocab = VocabZHSprite(i, self._vocabzhbankgroup)
                self._vocabengroup.add(ENvocab)
                self._vocabzhbankgroup.add(ZHvocab)
                ENvocab.twin = ZHvocab
            else: ENvocab.kill()

    def __add_ZH_draw_vocab(self):
        amount_per_space = round(self._area / ((self._global_data.window_size[0]*self._global_data.window_size[1])/(consts.MAX_VOCAB_ACTIVE*2)))
        amount_per_space = amount_per_space if amount_per_space < consts.MAX_VOCAB_ACTIVE else consts.MAX_VOCAB_ACTIVE
        
        if len(self._vocabzhdrawgroup.sprites()) < amount_per_space and len(self._vocabzhbankgroup.sprites()):
            temp = next((sp for sp in self._vocabzhbankgroup.sprites() if sp.twin.is_presented), self._vocabzhbankgroup.sprites()[0])
            placement = randomize_vacant_location(temp, self._global_data.window_size, self._mask)

            if (placement):
                self._vocabzhdrawgroup.add(temp)
                temp.remove(self._vocabzhbankgroup)

    def __check_collision(self, group):
        to_publish = []
        for sp in group.sprites():
            if sp.is_out_of_bounds:
                sp.on_collision(sp.area)
                continue
            
            overlap_area = self._mask.overlap_area(sp.mask, (sp.rect.x, sp.rect.y))
            msg = sp.on_collision(overlap_area)
            if msg: to_publish.append(msg)  
        return to_publish      

    def __vocab_matching(self): 
        matched = []
        for sp in self._vocabzhdrawgroup.sprites():
            collides = pygame.sprite.collide_mask(sp, sp.twin)
            if collides:
                matched.append({"type": consts.MQTT_DATA_ACTIONS.MATCHED.value, "word": sp.as_dict})
                sp.match_success()
                self._logger.info(f'disappeared word: {sp.vocabZH}/{sp.vocabEN}; left words: {len(self._vocabengroup.sprites())}')
                if len(self._vocabengroup.sprites()) == 0: matched.append(self.__finish_game())
        return matched

    def __finish_game(self):
        self._logger.info("game finished!")
        self.__status=consts.GAME_STATUS.DONE
        return {"type": consts.MQTT_DATA_ACTIONS.STATUS.value, "word": consts.GAME_STATUS.DONE.value}

    def start_game(self):
        if(len(self._vocabengroup.sprites())):
            self.__status=consts.GAME_STATUS.ACTIVE
        else:
            self.__init_game()

    def pause_game(self):
        self.__status=consts.GAME_STATUS.HALTED

    def stop_game(self):
        self.__status=consts.GAME_STATUS.HALTED
        [spg.empty() for spg in self.__all_spritegroups]
    
    def spin_words(self) -> None:
        [[sp.spin_word() for sp in spg.sprites()] for spg in self.__all_spritegroups]

    def __logic_stage(self) -> list:
        self.__setup_mask()

        to_publish= self.__vocab_matching()
        self.__add_ZH_draw_vocab()

        self.__check_collision(self._vocabzhdrawgroup)
        to_publish+= self.__check_collision(self._vocabengroup)

        return to_publish

    def __render_stage(self):
        self._vocabzhdrawgroup.update()
        self._vocabzhdrawgroup.draw(self._window)
        self._vocabengroup.draw(self._window)

    def game_loop(self):
        if self.__status == consts.GAME_STATUS.ACTIVE:
            to_publish = self.__logic_stage()
            if len(to_publish): self._eventbus.publish(consts.MQTT_TOPIC_DATA, to_publish)
            self.__render_stage()
