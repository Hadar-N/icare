import pygame
import json
from random import sample, randint

from game_shared import VocabItem, GAME_MODES, GAME_LEVELS

import utils.consts as consts

def vocab_to_vocab_dict(item: dict, mode: GAME_MODES) -> VocabItem:
        if mode == GAME_MODES.ENtoZH.value:
            item["similar"] = item["zh_options"]
        else:
            temp_meaning = item["meaning"]
            item["meaning"] = item["word"]
            item["word"] = temp_meaning
            item["similar"] = item["en_options"]

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

def random_location_in_window(sprite: pygame.sprite.Sprite, window_size: tuple[int]) -> int:
        return randint(consts.CLEAN_EDGES, window_size[0] - consts.CLEAN_EDGES - sprite.rect.width), randint(consts.CLEAN_EDGES, window_size[1] - consts.CLEAN_EDGES - sprite.rect.height)

def randomize_vacant_location(sprite: pygame.sprite.Sprite, window_size: tuple[int], mask: pygame.mask.Mask, group : pygame.sprite.Group = None) -> bool:
        def location_condition(rect): 
            return pygame.sprite.spritecollide(sprite, group, False) if type(group) == pygame.sprite.Group else mask.overlap(sprite.mask, (rect.x,rect.y))

        count = consts.MAX_PLACEMENT_ATTAMPTS
        sprite.set_location(random_location_in_window(sprite, window_size))
        
        while location_condition(sprite.rect) and count > 0:
            sprite.set_location(random_location_in_window(sprite, window_size))
            count-=1

        return count > 0
