import cv2
import pygame
import utils.consts as consts
from utils.internals_management_helpers import createFishSprite, checkCollision

class ContourPolygon(pygame.sprite.Sprite):
    def __init__(self, contour, resize_proportion):
        super().__init__()
        self.resize_proportion = resize_proportion
        self.color = (10,10,10)
        self.setShape(contour)
        self.internal_sprites = pygame.sprite.Group()

        self.decideHowManyKids()

    # def isSpriteBigEnoughToHaveInternal(self):
    #     w,h = consts.FISH_SIZE
    #     return self.rect.height > h and self.rect.width > w

    def updateShape(self, contour):
        self.setShape(contour)
        return self
    
    def decideHowManyKids(self):
        if not hasattr(self, 'internal_sprites'):
            self.internal_sprites = pygame.sprite.Group()
        
        internal_amount = len(self.internal_sprites.sprites())
        wanted_amount = int((self.area / (consts.FISH_SIZE[0]*consts.FISH_SIZE[1])) / consts.FREE_AREA_FOR_FISH)

        # if (internal_amount > wanted_amount):
        #     for i in range(wanted_amount, internal_amount):
        #         self.internal_sprites.sprites()[i].kill()
        # elif internal_amount < wanted_amount:
        if internal_amount < wanted_amount:
            for i in range(internal_amount, wanted_amount):
                sp = self.FishSprite()
                if sp:
                    self.internal_sprites.add(sp)
    
    def FishSprite(self):
        # if not self.isSpriteBigEnoughToHaveInternal():
        #     return None
        
        return createFishSprite(self.inv_mask, (self.rect.width, self.rect.height))

    def setShape(self, contour): 
        bounding = list(map(lambda x: int(x * self.resize_proportion), cv2.boundingRect(contour)))
        x = bounding[consts.BOUND_LEGEND["X"]]
        y = bounding[consts.BOUND_LEGEND["Y"]]
        points = [(int(point[0][0] * self.resize_proportion) - x, int(point[0][1] * self.resize_proportion) - y) for point in contour]

        self.image = pygame.Surface((bounding[consts.BOUND_LEGEND["WIDTH"]], bounding[consts.BOUND_LEGEND["HEIGHT"]]), pygame.SRCALPHA)
        self.rect = pygame.draw.polygon(self.image, self.color, points)
        self.mask = pygame.mask.from_threshold(self.image, self.color, threshold=(1, 1, 1))
        self.inv_mask = pygame.mask.from_threshold(self.image, self.color, threshold=(1, 1, 1))
        pygame.mask.Mask.invert(self.inv_mask)

        self.contour = contour
        self.area = cv2.contourArea(contour)
        self.rect.x = x
        self.rect.y = y
        self.rect.height = bounding[consts.BOUND_LEGEND["HEIGHT"]]
        self.rect.width = bounding[consts.BOUND_LEGEND["WIDTH"]]

        # self.decideHowManyKids()

    def update(self):
        checkCollision(self.internal_sprites, self.inv_mask, (self.rect.width, self.rect.height))
        self.internal_sprites.update()
        self.internal_sprites.draw(self.image)

