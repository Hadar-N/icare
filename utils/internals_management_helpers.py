import pygame
import numpy as np
from random import randint
from utils.consts import *
from utils.dataSingleton import DataSingleton
from sprites.FishSprite import FishSprite

def getFishOptions():
    def getfish(p):
        img = pygame.image.load(p).convert_alpha()
        width = FISH_SIZE_WIDTH_RANGE[1]
        img_orig_size = img.get_rect()
        height = (img_orig_size[BOUND_LEGEND["HEIGHT"]]/img_orig_size[BOUND_LEGEND["WIDTH"]])*width
        return pygame.transform.scale(img, (width, height))

    fish = [getfish(p) for p in FISH_SPRITE_IMGS_PATHS]

    return fish

def AddSpritesToGroup(internals, mask, area):
    internal_amount = len(internals.sprites())
    avg_fish_width = np.average(FISH_SIZE_WIDTH_RANGE)
    wanted_amount = int(area/((avg_fish_width**2)*FREE_AREA_FOR_FISH))

    if internal_amount < wanted_amount:
        for i in range(internal_amount, wanted_amount):
            sp = createFishSprite(mask)
            if sp:
                internals.add(sp)
    elif internal_amount> 0 and internal_amount > wanted_amount:
        [internals.sprites()[i].removeSelf() for i in range(wanted_amount, internal_amount)]

def createFishSprite(mask, contour_size = None):
    global_data = DataSingleton()
    fish_index = randint(0, len(global_data.fish_options) - 1)
    chosen_fish = global_data.fish_options[fish_index]
    if not contour_size: contour_size = global_data.window_size
    sprite = FishSprite(chosen_fish)
    placement = randomizeInternalLocation(mask, sprite, contour_size)

    if (placement):
        sprite.rect.x, sprite.rect.y = placement
        sprite.interval = INTERVALS_MAJ[fish_index]
    else:
        return None

    return sprite

def randomizeInternalLocation(mask, sprite, window_size):
    def random_location():
        return (randint(0, window_size[0] - sprite.rect.height), randint(0, window_size[1] - sprite.rect.width))

    x,y = random_location()
    count = MAX_PLACEMENT_ATTAMPTS

    while mask.overlap(sprite.mask, (x, y)) and count > 0:
        x,y = random_location()
        count-=1

    return (x,y) if count > 0 else None    

def checkCollision(spriteGroup, mask, contour_size):
    justFlipped= []
    for sp in spriteGroup.sprites():

        isOutOfBounds = sp.rect.x < 0 or sp.rect.y < 0 or sp.rect.x + sp.rect.width > contour_size[0] or sp.rect.y + sp.rect.height > contour_size[1]
        if isOutOfBounds:
            sp.flipDirection()
            if not sp.isDeleting: justFlipped.append(sp)
            continue

        area = mask.overlap_area(sp.mask, (sp.rect.x, sp.rect.y))
        if area:
            sp.flipDirection()
            if not sp.isDeleting: justFlipped.append(sp)
    return justFlipped

