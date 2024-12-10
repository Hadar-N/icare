import json
import pygame
import pyttsx3
import numpy as np
from random import sample
from utils.consts import *
from utils.dataSingleton import DataSingleton
from sprites.VocabENSprite import VocabENSprite
from sprites.VocabZHSprite import VocabZHSprite
from .internals_management_helpers import randomizeInternalLocation, randomizeUniqueLocations

def initVocabOptions():
    globaldata = DataSingleton()
    globaldata.vocab_font = pygame.font.Font(FONT_PATH, FONT_SIZE)
    globaldata.espeak_engine = pyttsx3.init(driverName='espeak') if globaldata.env == "pi" else pyttsx3.init()

    with open(VOCAB_PATH, 'r', encoding="utf8") as file:
        data = json.load(file)
        globaldata.vocab_options = sample(data['vocab'], VOCAB_AMOUNT)

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

def vocabMatching(logger, enggroup,zhactivegroup): 
    for sp in zhactivegroup.sprites():
        collides = pygame.sprite.spritecollide(sp,enggroup,False)
        if collides:
            relevant = next((c_sp for c_sp in collides if c_sp.vocabZH == sp.vocabZH and c_sp.vocabEN == sp.vocabEN), None)
            if relevant:
                relevant.matchSuccess()
                sp.matchSuccess()
                logger.info(f'disappeared word: {sp.vocabZH}/{relevant.vocabEN}; left words: {len(enggroup.sprites())}')
                if len(enggroup.sprites()) == 0: finishGame(logger)

def finishGame(logger):
    logger.info("game finished!")
    print("finished!!!")
        