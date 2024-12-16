import json
import pygame
import pyttsx3
from random import sample, randint
from utils.consts import *
from utils.dataSingleton import DataSingleton
from sprites.VocabENSprite import VocabENSprite
from sprites.VocabZHSprite import VocabZHSprite

def initVocabOptions():
    globaldata = DataSingleton()
    globaldata.vocab_font = globaldata.vocab_font if globaldata.vocab_font else pygame.font.Font(FONT_PATH, FONT_SIZE)
    globaldata.espeak_engine = globaldata.espeak_engine if globaldata.espeak_engine else (pyttsx3.init(driverName='espeak') if globaldata.env == "pi" else pyttsx3.init())

    with open(VOCAB_PATH, 'r', encoding="utf8") as file:
        data = json.load(file)
        globaldata.vocab_options = sample(data, VOCAB_AMOUNT)

def AddVocabToGroup(static, bank):
    globaldata = DataSingleton()
    for i in range(VOCAB_AMOUNT):
        ENvocab = VocabENSprite(i)
        location = randomizeUniqueLocations(static,ENvocab, globaldata.window_size)
        if (location):
            static.add(ENvocab)
            bank.add(VocabZHSprite(i, bank))
        else: ENvocab.kill()

def presentNewZHVocab(bank, active, mask, area):
    globaldata = DataSingleton()
    amount_per_space = round(area / ((globaldata.window_size[0]*globaldata.window_size[1])/(MAX_VOCAB_ACTIVE*2)))
    amount_per_space = amount_per_space if amount_per_space < MAX_VOCAB_ACTIVE else MAX_VOCAB_ACTIVE
    
    if len(active.sprites()) < amount_per_space and len(bank.sprites()):
        temp = bank.sprites()[0]
        placement = randomizeInternalLocation(mask, temp, globaldata.window_size)

        if (placement):
            temp.setLocation(placement)
            active.add(temp)
            temp.remove(bank)

def vocabReadMaskCollision(spriteGroup, mask):
    for sp in spriteGroup.sprites():
        area = mask.overlap_area(sp.mask, (sp.rect.x, sp.rect.y))
        sp.changeIsPresented(area>sp.area/2)

def random_location(sprite, window_size):
    return randint(CLEAN_EDGES, window_size[0] - CLEAN_EDGES - sprite.rect.width), randint(CLEAN_EDGES, window_size[1] - CLEAN_EDGES - sprite.rect.height)

def randomizeUniqueLocations(group, sprite, window_size):
    sprite.setLocation(random_location(sprite, window_size))
    count = MAX_PLACEMENT_ATTAMPTS

    while pygame.sprite.spritecollide(sprite, group, False) and count > 0:
        sprite.setLocation(random_location(sprite, window_size))
        count-=1

    return True if count > 0 else False

def randomizeInternalLocation(mask, sprite, window_size):
    x,y = random_location(sprite, window_size)
    count = MAX_PLACEMENT_ATTAMPTS

    while mask.overlap(sprite.mask, (x, y)) and count > 0:
        x,y = random_location(sprite, window_size)
        count-=1

    return (x,y) if count > 0 else None    
