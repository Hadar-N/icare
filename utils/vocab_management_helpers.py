import json
import pygame
import pyttsx3
from random import sample
from utils.consts import *
from utils.dataSingleton import DataSingleton
from sprites.VocabENSprite import VocabENSprite

def initVocabOptions():
    globaldata = DataSingleton()
    globaldata.vocab_font = pygame.font.SysFont(None, FONT_SIZE)
    globaldata.espeak_engine = pyttsx3.init(driverName='espeak')

    with open(VOCAB_PATH, 'r') as file:
        data = json.load(file)
        globaldata.vocab_options = sample(data['vocab'], VOCAB_AMOUNT)

def AddVocabToGroup(internals):
    [internals.add(createWordSprite(i)) for i in range (0,VOCAB_AMOUNT - 1)]

def createWordSprite(vocab_i = 0):
    sprite = VocabENSprite(vocab_i)
    print(sprite.vocabEN, sprite.rect)

    return sprite

def vocabMaskCollision(spriteGroup, mask):
    for sp in spriteGroup.sprites():
        area = mask.overlap_area(sp.mask, (sp.rect.x, sp.rect.y))
        sp.changeIsPresented(area>sp.area/2)
