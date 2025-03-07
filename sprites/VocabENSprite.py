from utils.consts import MQTT_DATA_ACTIONS
from .GenVocabSprite import GenVocabSprite

class VocabENSprite(GenVocabSprite):
    def __init__(self, vocab_i: object):
        super().__init__(vocab_i, "en")

        self.__is_presented = False
            
    @property
    def is_presented(self): return self.__is_presented
    @property
    def is_out_of_bounds(self): return False

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