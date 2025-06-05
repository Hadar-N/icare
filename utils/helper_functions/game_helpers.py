import json
from random import sample

from game_shared import VocabItem, GAME_MODES, GAME_LEVELS

import utils.consts as consts

def vocab_to_vocab_dict(item: dict, mode: GAME_MODES) -> VocabItem:
        if mode == GAME_MODES.ENtoZH.value:
            item["similar"] = item["zh_options"]
        elif mode == GAME_MODES.ZHtoEN.value:
            temp_meaning = item["meaning"]
            item["meaning"] = item["word"]
            item["word"] = temp_meaning
            item["similar"] = item["en_options"]
        elif mode == GAME_MODES.ENtoSpelling:
            item["similar"] = item["spelling_options"]
            item["meaning"] = item["word"]

        return VocabItem(**item)

def filter_by_level(arr: list[dict], level: GAME_LEVELS) -> list[dict]:
        res = arr
        if level == GAME_LEVELS.BEGINNER.value:
            res = [r for r in res if r["level"] == GAME_LEVELS.BEGINNER.value]
        elif level == GAME_LEVELS.INTERMEDIATE.value:
            res = [r for r in res if r["level"] != GAME_LEVELS.ADVANCED.value]
        return res

def init_vocab_options(level, mode) -> list[dict]:
        with open(consts.VOCAB_PATH, 'r', encoding="utf8") as file:
            data = json.load(file)
            data = filter_by_level(data, level)
            vocab_options = sample(data, consts.VOCAB_AMOUNT)
        return [vocab_to_vocab_dict(item, mode) for item in vocab_options]
