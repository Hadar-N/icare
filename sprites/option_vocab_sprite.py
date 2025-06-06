from game_shared import MQTT_DATA_ACTIONS
from mqtt_shared import Topics

from utils.consts import *
from .gen_vocab_sprite import GenVocabSprite

class OptionVocabSprite(GenVocabSprite):
    def __init__(self, vocab, eventbus):
        super().__init__(vocab, eventbus)
    
    @property
    def vocabSelf(self): return self.vocabTranslation
    @property
    def _get_color(self): return (255,0,255)
    
    def test_match(self):
        if self.vocabTranslation == self.twin.vocabTranslation:
            self.match_success()
            self._eventbus.publish(Topics.word_state(), {"type": MQTT_DATA_ACTIONS.MATCHED, "word": self.as_dict()})
        else:
            self.twin.turn_option_off(self.vocabTranslation)
            self._eventbus.publish(Topics.word_state(), {"type": MQTT_DATA_ACTIONS.STATUS, "word": self.twin.as_dict()})
            self.twin = None
            self.remove_self(REMOVAL_REASON.MATCH_FAIL)
            