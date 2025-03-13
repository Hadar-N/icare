from random import sample, randint

from utils.consts import MQTT_DATA_ACTIONS
from .gen_vocab_sprite import GenVocabSprite

class MainVocabSprite(GenVocabSprite):
    def __init__(self, vocab: dict):
        super().__init__(vocab)

        self.__is_presented = False
        self.__options = []

        self.apply_options_list()
            
    @property
    def vocabSelf(self): return self.vocabMain
    @property
    def _get_color(self): return (0,0,255)
    @property
    def as_dict(self): 
        base_dict = super().as_dict
        base_dict["options"] = [self.__options]
        return base_dict
    @property
    def options(self): return self.__options

    @property
    def is_presented(self): return self.__is_presented
    @property
    def is_out_of_bounds(self): return False

    def apply_options_list(self):
        temp = sample(self._vocab["similar"], 2)
        ix = randint(0,2)
        temp.insert(ix, self.vocabTranslation)
        self.__options = temp

    def on_collision(self, area_collision: int) -> object | None:
        new_presented = area_collision<self.area/4
        to_publish = None

        if new_presented and not self.__is_presented:
            to_publish = { "type": MQTT_DATA_ACTIONS.NEW.value, "word": self.as_dict }
            # self._global_data.espeak_engine.say(f'{self._vocab["en"]} .')
            # self._global_data.espeak_engine.runAndWait()
        elif self.__is_presented and not new_presented:
            to_publish = { "type": MQTT_DATA_ACTIONS.REMOVE.value, "word": self.as_dict }
        
        self.__is_presented = new_presented
        return to_publish