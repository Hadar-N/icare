import subprocess
import json
import sys
import pygame
import os
from dotenv import load_dotenv

from utils.consts import CAMERA_RES, FONT_PATH, FONT_SIZE, CLOCK
from utils.helper_functions import setCameraFunction

load_dotenv(verbose=True, override=True)

class BtnItem():
    def __init__(self, txt, item_no, font, screen_size):
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

def refresh_action(take_picture):
    global image
    global boundaries
    image = take_picture()
    boundaries= []


def run_calibration():
    screen_size = [int(i / 2) for i in CAMERA_RES]

    boundaries = []
    take_picture, remove_camera = setCameraFunction(os.getenv("ENV"), screen_size[::-1])

    os.environ["DISPLAY"] = ":10"
    pygame.init()
    screen = pygame.display.set_mode(screen_size)
    clock = pygame.time.Clock()

    image = take_picture()
    btns_texts = {
        "refresh": lambda: refresh_action(take_picture),
        "submit": lambda: save_and_launch_game(boundaries)
    }
    font = pygame.font.Font(FONT_PATH, int(FONT_SIZE/1.5))

    rects = [BtnItem(list(btns_texts.keys())[i], i, font, screen_size) for i in range(0, len(btns_texts))]

    running = True
    while running:
        screen.fill((0,0,0))
        screen.blit(pygame.surfarray.make_surface(image), (0,0))
        [r.draw_btn(screen) for r in rects]

        pygame.display.update()
        clock.tick(CLOCK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos=pygame.mouse.get_pos()
                collided = next((r for r in rects if r.is_colliding(pos)), None)
                if collided:
                    # print("collided!!!", collided, collided.content)
                    btns_texts[collided.content]()
                else:
                    print (f"x = {pos[0]}, y = {pos[1]}", boundaries)

    pygame.quit()
    sys.exit()
    remove_camera()


def save_and_launch_game(boundaries):
    print("save_and_launch_game: ", boundaries)

if __name__ == "__main__":
    run_calibration()