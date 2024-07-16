from random import randint
from utils.consts import FISH_SIZE, FREE_AREA_FOR_FISH, MAX_PLACEMENT_ATTAMPTS
from sprites.InternalSprite import InternalSprite

def AddSpritesToGroup(internals, mask, area, window_size):
    internal_amount = len(internals.sprites())
    wanted_amount = int(area/((FISH_SIZE[0]*FISH_SIZE[1])*FREE_AREA_FOR_FISH))

    if internal_amount < wanted_amount:
        for i in range(internal_amount, wanted_amount):
            sp = createFishSprite(mask, window_size)
            if sp:
                internals.add(sp)
    elif internal_amount > wanted_amount:
        for i in range(wanted_amount, internal_amount):
            internals.sprites()[i].kill()

def createFishSprite(mask,window_size):
    sprite = InternalSprite()
    placement = randomizeInternalLocation(mask, sprite, window_size)
    if (placement):
        sprite.rect.x, sprite.rect.y = placement
    else:
        return None

    return sprite

def randomizeInternalLocation(mask, sprite, window_size):
    def random_location():
        random_x = randint(0, window_size[0] - sprite.rect.height)
        random_y = randint(0, window_size[1] - sprite.rect.width)
        return (random_x, random_y)

    x,y = random_location()

    count = MAX_PLACEMENT_ATTAMPTS
    while mask.overlap(sprite.mask, (x, y)) and count > 0:
        x,y = random_location()
        count-=1

    return (x,y) if count > 0 else None    

def checkCollision(spriteGroup, mask, window_size):
    for sp in spriteGroup.sprites():
        isOutOfBounds = sp.rect.x < 0 or sp.rect.y < 0 or sp.rect.x + sp.rect.width > window_size[0] or sp.rect.y + sp.rect.height > window_size[1]
        if isOutOfBounds:
            sp.flipDirection()
            continue

        area = mask.overlap_area(sp.mask, (sp.rect.x, sp.rect.y))
        if area > sp.rect.width*sp.speed:
            sp.kill()
        elif area:
            sp.flipDirection()

