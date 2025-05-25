import cv2
import pygame
import math
import numpy as np
import time
from logging import Logger

import utils.consts as consts
from utils.data_singleton import DataSingleton
from .setup_helpers import asstr, get_terminal_params

global_data = DataSingleton()

def get_save_path(stage:str):
       return f"tests/extra-board-pics/img_{int(time.time())}_{stage}.jpg"

def get_blurred_picture(image: np.ndarray, matrix: np.ndarray, is_save:bool = False) -> np.ndarray:
        reference_image = cv2.flip(cv2.warpPerspective(image, matrix, (global_data.window_size[1], global_data.window_size[0]) ,flags=cv2.INTER_LINEAR), 0)
        if is_save:
               write_controured_img(image,[],get_save_path("a_initial"))
               write_controured_img(reference_image,[],get_save_path("b_focused"))
        return cv2.GaussianBlur(reference_image, consts.BLUR_SIZE, 0)

def write_controured_img(image: np.ndarray, coords: list[np.ndarray], path:str = consts.CONTOUR_IMAGE_LOC) -> None:
        if len(coords):
                cv2.polylines(image, [x.astype(np.int32) for x in coords], isClosed=True, color=(global_data.threshvalue, global_data.threshvalue, global_data.threshvalue), thickness=3)
        cv2.imwrite(path, image)

def is_pygame_pt_in_contour(cnt: np.ndarray, pt: tuple) -> bool:
       return cv2.pointPolygonTest(cnt, (pt[1], pt[0]), False) >= 0

def convert_contour_to_polygon(cnt: np.ndarray) -> list:
       return [[c[1], c[0]] for c in cnt.reshape(-1, 2)]

def calc_contour_midpoint(cnt: np.ndarray) -> tuple:
       M = cv2.moments(cnt)
       m00 = max(M["m00"], 1)
       return (int(M["m01"] / m00), int(M["m10"] / m00))

def find_uncovered_contours(img: np.ndarray) -> list[dict]:
        contours, hirar = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        is_uncovered = np.zeros(len(contours))
        children_areas = np.zeros(len(contours))
    
        def apply_to_all_levels(ix: int, start_val: bool):
                curr_ix = ix
                level_counter = int(start_val)
                while curr_ix != -1 and not is_uncovered[curr_ix]:
                        parent_ix = hirar[0][curr_ix][consts.HIRAR_LOCATIONS.PARENT.value]
                        if bool(level_counter%2):
                                is_uncovered[curr_ix] = True
                        else:
                                is_uncovered[curr_ix] = False
                                if parent_ix != -1: children_areas[parent_ix]+=cv2.contourArea(contours[curr_ix])
                        curr_ix = parent_ix
                        level_counter+=1

        for i in range(0, len(contours)):
                if hirar[0][i][consts.HIRAR_LOCATIONS.CHILD.value] == -1:
                        midpoint = calc_contour_midpoint(contours[i])
                        apply_to_all_levels(i, np.mean(img[*midpoint]) > 250)

        return [c for c in 
                [{"contour": contours[i], "area": cv2.contourArea(contours[i]) - children_areas[i]} for i in range(0,len(contours)) if is_uncovered[i]]
                if c["area"] > global_data.threshsize]
                        
def create_mask(current_image: np.ndarray, reference_blur: np.ndarray, is_save:bool= False) -> pygame.mask.Mask:
        difference = cv2.absdiff(current_image, reference_blur)
        gray_image = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
        _, thresholded = cv2.threshold(gray_image, global_data.threshvalue, consts.THRESHOLD_MAX, cv2.THRESH_BINARY)
        mask_img = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, consts.KERNEL)
        contours_information = find_uncovered_contours(mask_img)
        if is_save:
               write_controured_img(current_image,[],get_save_path("c_blurred"))
               write_controured_img(difference,[],get_save_path("d_diffed"))
               write_controured_img(gray_image,[],get_save_path("e_grayed"))
               write_controured_img(thresholded,[],get_save_path("f_thresholded"))
               write_controured_img(mask_img,[],get_save_path("g_closed"))
               if len(contours_information): write_controured_img(mask_img,contours_information[0]["contour"],get_save_path("i_contoured"))
        
        mask_img_rgb = pygame.surfarray.make_surface(cv2.cvtColor(mask_img, cv2.COLOR_GRAY2RGB))
        return pygame.mask.from_threshold(mask_img_rgb, (0,0,0), threshold=(1,1,1)), contours_information

def set_transformation_matrix(ref: np.ndarray) -> tuple[np.ndarray]:
        coordinates = ref

        if not coordinates:
                relative_coords, in_win_size = get_terminal_params()
                relative_x, relative_y = [in_win_size[i] / global_data.img_resize[i] for i in range (0,len(in_win_size))]
                coordinates = (relative_coords.astype(np.float32) / [relative_x, relative_y]).astype(int)

        ordered_points_in_board = sort_points([item[0] for item in coordinates])
        
        inp_coords =  np.float32(ordered_points_in_board)
        out_coords =  np.float32([[0,0], [0, global_data.window_size[0] - 1], [global_data.window_size[1] - 1, global_data.window_size[0] - 1], [global_data.window_size[1] - 1, 0]])
        global_data.threshsize = cv2.contourArea(out_coords)/consts.MIN_FRAME_CONTENT_PARTITION

        matrix = cv2.getPerspectiveTransform(inp_coords, out_coords)

        return inp_coords, out_coords, matrix

def set_compare_values(takePicture: callable, matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        new_img = takePicture()
        reference_blur = get_blurred_picture(new_img, matrix)
        global_data.threshvalue = find_threshval(reference_blur)
        global_data.logger.info(f'calculated threshvalue={global_data.threshvalue} with threshsize={global_data.threshsize}')

        return reference_blur, new_img

def find_threshval(empty_image: np.ndarray, multip: float = consts.THRESHOLD_MULTIP) -> float:
        return max(consts.THRESHOLD_MIN, np.mean(empty_image) + (np.std(empty_image) * multip))

def sort_points(points : list[float]) -> list[float]:
    points = np.array(points)
    sums = points.sum(axis=1)  # x + y
    diffs = np.diff(points, axis=1)[:, 0]

    sorted_points = np.zeros((4, 2), dtype=np.float32)
    sorted_points[0] = points[np.argmin(sums)]  # Top-left
    sorted_points[1] = points[np.argmax(diffs)]  # Bottom-left
    sorted_points[2] = points[np.argmax(sums)]  # Bottom-right
    sorted_points[3] = points[np.argmin(diffs)]  # Top-right

    if math.dist(sorted_points[0], sorted_points[1]) < math.dist(sorted_points[0], sorted_points[3]):
        sorted_points = [sorted_points[0],sorted_points[3], sorted_points[2], sorted_points[1]]

    return sorted_points
