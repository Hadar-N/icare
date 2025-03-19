from random import sample, randint

from game_shared import MQTT_DATA_ACTIONS
from mqtt_shared import Topics
from .gen_vocab_sprite import GenVocabSprite

class MainVocabSprite(GenVocabSprite):
    def __init__(self, vocab: dict, eventbus):
        super().__init__(vocab, eventbus)

        self.__is_presented = False
            
    @property
    def vocabSelf(self): return self.vocabMain
    @property
    def _get_color(self): return (0,0,255)
    @property
    def options(self): return self._vocab.options

    @property
    def is_presented(self): return self.__is_presented
    @property
    def is_out_of_bounds(self): return False

    def turn_option_off(self, selected: str) -> None:
        opt = next((x for x in self._vocab.options if x.word.lower() == selected.lower()), None)
        if opt: opt.is_attempted = True

    def on_collision(self, area_collision: int) -> None:
        new_presented = area_collision<self.area/4
        change_type = None

        if new_presented and not self.__is_presented:
            change_type = MQTT_DATA_ACTIONS.NEW
            # self._global_data.espeak_engine.say(f'{self._vocab["en"]} .')
            # self._global_data.espeak_engine.runAndWait()
        elif self.__is_presented and not new_presented:
            change_type = MQTT_DATA_ACTIONS.REMOVE
        if change_type and self._eventbus: self._eventbus.publish(Topics.word_state(), {"type": change_type, "word": self.as_dict()})
        
        self.__is_presented = new_presented
