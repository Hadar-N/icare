import pygame
import json
from random import sample, randint
from functools import partial

import utils.consts as consts

def init_vocab_options(global_data) -> None:
        global_data.vocab_font = pygame.font.Font(consts.FONT_PATH, consts.FONT_SIZE)
        # self._global_data.espeak_engine = pyttsx3.init(driverName='espeak') if self._global_data.env == "pi" else pyttsx3.init()

        with open(consts.VOCAB_PATH, 'r', encoding="utf8") as file:
            data = json.load(file)
            global_data.vocab_options = sample(data, consts.VOCAB_AMOUNT)

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
