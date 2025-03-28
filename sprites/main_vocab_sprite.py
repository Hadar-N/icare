from random import sample, randint

from game_shared import MQTT_DATA_ACTIONS
from mqtt_shared import Topics
from .gen_vocab_sprite import GenVocabSprite

class MainVocabSprite(GenVocabSprite):
    def __init__(self, vocab: dict, eventbus):
        super().__init__(vocab, eventbus)

        self.on_appearing()
            
    @property
    def vocabSelf(self): return self.vocabMain
    @property
    def _get_color(self): return (0,255,0)
    @property
    def options(self): return self._vocab.options

    def turn_option_off(self, selected: str) -> None:
        opt = next((x for x in self._vocab.options if x.word.lower() == selected.lower()), None)
        if opt: opt.is_attempted = True

    def on_appearing(self) -> None:
        if self._eventbus: self._eventbus.publish(Topics.word_state(), {"type": MQTT_DATA_ACTIONS.NEW, "word": self.as_dict()})
    
    def on_deleting(self) -> None:
        if self._eventbus: self._eventbus.publish(Topics.word_state(), {"type": MQTT_DATA_ACTIONS.REMOVE, "word": self.as_dict()})
