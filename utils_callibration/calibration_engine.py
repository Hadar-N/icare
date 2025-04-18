import pygame

from utils import DataSingleton
from utils.consts import FONT_PATH, FONT_SIZE, CLOCK
from utils.helper_functions import setCameraFunction
from utils_callibration.helper_funcs import detect_board_auto
from utils_callibration.helper_classes import Boundary, BtnItem

global_data = DataSingleton()

class CalibrationEngine():
    def __init__(self, nextstage: callable):
        pygame.init()
        self.__screen = pygame.display.set_mode(global_data.img_resize)
        self.__clock = pygame.time.Clock()

        self.__nextstage = nextstage

        self.__take_picture, self.__remove_camera = setCameraFunction(global_data.env, global_data.img_resize[::-1])
        self.__image = self.__take_picture()
        self.__boundaries = pygame.sprite.Group()

        self.__font = pygame.font.Font(FONT_PATH, int(FONT_SIZE/1.5))
        
        self.__rects = self.__create_btn_rects()
        self.__running = True

    def __create_btn_rects(self):
        btns_texts = {
            "refresh": self.__refresh_action,
            "submit": self.__save_and_launch_game
        }
        return [BtnItem(text, i, self.__font, callback) for i, (text, callback) in enumerate(btns_texts.items())]

    def __refresh_action(self):
        self.__image = self.__take_picture()
        self.__boundaries.empty()

    def __initial_callibration(self):
        coords = detect_board_auto(self.__image)
        is_full_display = [0,0] in coords and [i - 1 for i in global_data.window_size] in coords
        if len(coords) and not is_full_display:
            for i in coords:
                self.__boundaries.add(Boundary(i[0]))

    def __save_and_launch_game(self):
        if len(self.__boundaries.sprites()) == 4:
            self.__nextstage([b.center_point for b in self.__boundaries.sprites()])
            self.__running = False
        else: print("invalid points- should be 4 items!")

    def __gameloop_content(self):
        self.__screen.fill((0,0,0))
        self.__screen.blit(pygame.surfarray.make_surface(self.__image), (0,0))
        [r.draw_btn(self.__screen) for r in self.__rects]
        self.__boundaries.draw(self.__screen)

        self.__clock.tick(CLOCK)
        pygame.display.update()

    def __game_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.__running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos=pygame.mouse.get_pos()
                collided = next((r for r in self.__rects if r.is_colliding(pos)), None)
                if collided:
                    collided.callback()
                else:
                    collided_pt = next((p for p in self.__boundaries.sprites() if p.is_colliding(pos)), None)
                    if (collided_pt): collided_pt.kill()
                    else: self.__boundaries.add(Boundary(pos))

    def engine_loop(self):
        self.__initial_callibration()

        while self.__running:
            self.__gameloop_content()
            self.__game_events()

        pygame.quit()
        self.__remove_camera()


