import pygame
from utils.consts import *

def checkCollision(spriteGroup, mask):
    justFlipped= []
    for sp in spriteGroup.sprites():
        if sp.isOutOfBounds:
            sp.flipDirection()
            if not sp.isDeleting: justFlipped.append(sp)
            continue

        area = mask.overlap_area(sp.mask, (sp.rect.x, sp.rect.y))
        if area:
            sp.flipDirection()
            if not sp.isDeleting: justFlipped.append(sp)
    return justFlipped

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
        