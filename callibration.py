import subprocess
import json
import sys
import pygame
import os
from dotenv import load_dotenv

from utils.consts import CAMERA_RES, FONT_PATH, FONT_SIZE, CLOCK
from utils.helper_functions import setCameraFunction

load_dotenv(verbose=True, override=True)
env = os.getenv("ENV")

pygame.init()

screen_size = [int(i / 2) for i in CAMERA_RES]
take_picture, remove_camera = setCameraFunction(env, screen_size[::-1])
image = take_picture()
boundaries = pygame.sprite.Group()

BOUNDARY_RADIUS = 5

class BtnItem():
    def __init__(self, txt, item_no, font):
        self.__rect = pygame.Rect(screen_size[0]/2 - 50, screen_size[1]/2 + item_no*50, 100, 50)
        self.__color = (200,200,200)
        self.__content = txt
        self.__text_obj = font.render(txt, True, (0,0,0))

    @property
    def content(self): return self.__content

    def draw_btn(self, screen):
        pygame.draw.rect(screen, self.__color, self.__rect)
        screen.blit(self.__text_obj, (self.__rect[0], self.__rect[1]))

    def is_colliding(self, pos):
        x_colliding = pos[0] > self.__rect[0] and pos[0] < self.__rect[0] + self.__rect[2]
        y_colliding = pos[1] > self.__rect[1] and pos[1] < self.__rect[1] + self.__rect[3]
        return x_colliding and y_colliding

class Boundary(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.center_point = pos
        self.image = pygame.Surface(screen_size, flags=pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255,0,0), pos, BOUNDARY_RADIUS)
        self.rect = self.image.get_rect()

def refresh_action() :
    globals()["image"] = take_picture()
    globals()["boundaries"].empty()

def run_calibration():
    global boundaries
    global image

    os.environ["DISPLAY"] = ":10"
    screen = pygame.display.set_mode(screen_size)
    clock = pygame.time.Clock()
    
    btns_texts = {
        "refresh": refresh_action,
        "submit": save_and_launch_game
    }
    font = pygame.font.Font(FONT_PATH, int(FONT_SIZE/1.5))

    rects = [BtnItem(list(btns_texts.keys())[i], i, font) for i in range(0, len(btns_texts))]

    running = True
    while running:
        screen.fill((0,0,0))
        screen.blit(pygame.surfarray.make_surface(image), (0,0))
        [r.draw_btn(screen) for r in rects]
        boundaries.draw(screen)

        clock.tick(CLOCK)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos=pygame.mouse.get_pos()
                collided = next((r for r in rects if r.is_colliding(pos)), None)
                if collided:
                    btns_texts[collided.content]()
                else:
                    boundaries.add(Boundary(pos))

    pygame.quit()
    sys.exit()
    remove_camera()


def save_and_launch_game():
    print("save_and_launch_game: ", globals()["boundaries"])

if __name__ == "__main__":
    run_calibration()