import cv2
import pygame
import math
import numpy as np
from logging import Logger

import utils.consts as consts
from .setup_helpers import asstr

def get_blurred_picture(image: np.ndarray, matrix: np.ndarray, window_size: tuple[int]) -> np.ndarray:
        reference_image = cv2.flip(cv2.warpPerspective(image, matrix, (window_size[1], window_size[0]) ,flags=cv2.INTER_LINEAR), 0)
        return cv2.GaussianBlur(reference_image, consts.BLUR_SIZE, 0)

def write_controured_img(image: np.ndarray, coords: list[np.ndarray], threshvalue : int) -> None:
        cv2.polylines(image, [x.astype(np.int32) for x in coords], isClosed=True, color=(threshvalue, threshvalue, threshvalue), thickness=3)
        cv2.imwrite(consts.CONTOUR_IMAGE_LOC, image)

def is_pygame_pt_in_contour(cnt: np.ndarray, pt: tuple) -> bool:
       return cv2.pointPolygonTest(cnt, (pt[1], pt[0]), False) >= 0

def convert_contour_to_polygon(cnt: np.ndarray) -> list:
       return [[c[1], c[0]] for c in cnt.reshape(-1, 2)]

def calc_contour_midpoint(cnt: np.ndarray) -> tuple:
       M = cv2.moments(cnt)
       return (int(M["m01"] / M["m00"]), int(M["m10"] / M["m00"]))

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

        return [{"contour": contours[i], "area": cv2.contourArea(contours[i]) - children_areas[i]} for i in range(0,len(contours)) if is_uncovered[i]]
                        
def create_mask(current_image: np.ndarray, reference_blur: np.ndarray, threshvalue : int) -> pygame.mask.Mask:
        difference = cv2.absdiff(current_image, reference_blur)
        gray_image = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
        _, thresholded = cv2.threshold(gray_image, threshvalue, consts.THRESHOLD_MAX, cv2.THRESH_BINARY_INV)
        closed = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, consts.KERNEL)
        mask_img=cv2.bitwise_not(closed)
        contours_information = find_uncovered_contours(mask_img)
        mask_img_rgb = pygame.surfarray.make_surface(cv2.cvtColor(mask_img, cv2.COLOR_GRAY2RGB))
        return pygame.mask.from_threshold(mask_img_rgb, (0,0,0), threshold=(1,1,1)), contours_information

def set_transformation_matrix(global_data, ref = None) -> tuple[np.ndarray]:
        coordinates = ref if isinstance(ref, list) else None
        image = ref if isinstance(ref, np.ndarray) else None
    
        if not coordinates:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            thresholded = cv2.adaptiveThreshold(gray, consts.THRESHOLD_MAX, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,11,2)
            contours, _ = cv2.findContours(thresholded, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            coordinates = find_board(contours, global_data.img_resize)

        ordered_points_in_board = sort_points([item[0] for item in coordinates])
        
        inp_coords =  np.float32(ordered_points_in_board)
        out_coords =  np.float32([[0,0], [0, global_data.window_size[0] - 1], [global_data.window_size[1] - 1, global_data.window_size[0] - 1], [global_data.window_size[1] - 1, 0]])

        matrix = cv2.getPerspectiveTransform(inp_coords, out_coords)

        return inp_coords, out_coords, matrix

def get_transformation_matrix_with_borders(orig_inp_coords: np.ndarray, out_coords: np.ndarray, img_resize:tuple[int]) -> np.ndarray:
        middlepoint = orig_inp_coords.sum(axis=0)/4 # since we know the shape to be rectangle-like, we can assume the middlepoint to have 2 points on each side
        bordered_inp = np.float32(list(map(lambda i: np.array([max(i[0] - consts.BORDER_SIZE, 0.) if i[0] < middlepoint[0] else min(i[0] + consts.BORDER_SIZE, img_resize[0]),
                                                                max(i[1] - consts.BORDER_SIZE, 0.) if i[1] < middlepoint[1] else min(i[1] + consts.BORDER_SIZE, img_resize[1])])
                                                                , orig_inp_coords)))
        matrix = cv2.getPerspectiveTransform(bordered_inp, out_coords)

        return matrix, bordered_inp

def set_compare_values(takePicture: callable, matrix: np.ndarray, window_size: tuple[int], logger: Logger) -> tuple[np.ndarray, float, np.ndarray]:
        new_img = takePicture()
        reference_blur = get_blurred_picture(new_img, matrix, window_size)
        threshvalue_bordered = find_threshval(reference_blur)
        logger.info(f'calculated threshvalue by border={threshvalue_bordered}')

        return reference_blur, threshvalue_bordered, new_img

def find_threshval(empty_image: np.ndarray, multip: float = consts.THRESHOLD_MULTIP) -> float:
        return np.mean(empty_image) + (np.std(empty_image) * multip)

def find_board(conts: tuple, img_resize: tuple) -> np.ndarray:
        rects = []

        fake_contour = np.array([[img_resize[0] - 1, 0], [0,0], [0, img_resize[1] - 1],
                                 [img_resize[0] - 1, img_resize[1] - 1]]).reshape((-1,1,2)).astype(np.int32)
        full_area = cv2.contourArea(fake_contour)
        center_pt = (int(img_resize[0] / 2), int(img_resize[1] / 2))
        area_theshold = full_area/consts.MIN_FRAME_CONTENT_PARTITION

        for c in conts:
            epsilon = 0.02 * cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, epsilon, True)
            area= cv2.contourArea(approx)
            if len(approx) == 4 and area > area_theshold and area < full_area*.9:
                rects.append({"cnt": approx, "area": area})

        match len(rects):
            case 0: return fake_contour
            case 1: return rects[0]["cnt"]
            case _: return next((r for r in rects if is_pygame_pt_in_contour(r["cnt"], center_pt)), rects[0])["cnt"]

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
