import cv2
import pygame
import numpy as np
import utils.consts as consts

def get_blurred_picture(image: np.ndarray, matrix: np.ndarray, window_size: tuple[int]) -> np.ndarray:
        # image = cv2.resize(image, globaldata.img_resize)
        reference_image = cv2.flip(cv2.warpPerspective(image, matrix, (window_size[1], window_size[0]) ,flags=cv2.INTER_LINEAR), 0)
        return cv2.GaussianBlur(reference_image, consts.BLUR_SIZE, 0)

def write_controured_img(image: np.ndarray, coords: np.ndarray, threshvalue : int) -> None:
        cv2.polylines(image, [coords.astype(np.int32)], isClosed=True, color=(threshvalue, threshvalue, threshvalue), thickness=3)
        cv2.imwrite(consts.CONTOUR_IMAGE_LOC, image)

def create_mask(current_image: np.ndarray, reference_blur: np.ndarray, threshvalue : int) -> pygame.mask.Mask:
        # current_blurred = cv2.GaussianBlur(current_image, consts.BLUR_SIZE, 0)
        difference = cv2.absdiff(current_image, reference_blur)
        gray_image = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
        _, thresholded = cv2.threshold(gray_image, threshvalue, consts.THRESHOLD_MAX, cv2.THRESH_BINARY_INV)
        closed = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, consts.KERNEL)
        mask_img=cv2.bitwise_not(closed)
        mask_img_rgb = pygame.surfarray.make_surface(cv2.cvtColor(mask_img, cv2.COLOR_GRAY2RGB))
        return pygame.mask.from_threshold(mask_img_rgb, (0,0,0), threshold=(1,1,1))

def find_threshval(empty_image: np.ndarray, multip: float) -> float:
        return np.mean(np.mean(empty_image, axis=(0,1)), axis=0) * multip

def find_contours(image: np.ndarray) -> list:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        threshval = find_threshval(image, 1.)
        _, thresh = cv2.threshold(gray, threshval, consts.THRESHOLD_MAX, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

def find_board(conts: tuple, img_resize: tuple) -> np.ndarray:
        rects = []

        fake_contour = np.array([[img_resize[0] - 1, 0], [0,0], [0, img_resize[1] - 1],
                                 [img_resize[0] - 1, img_resize[1] - 1]]).reshape((-1,1,2)).astype(np.int32)
        full_area = cv2.contourArea(fake_contour)
        area_theshold = full_area/consts.MIN_FRAME_CONTENT_PARTITION

        for c in conts:
            epsilon = 0.02 * cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, epsilon, True)
            area= cv2.contourArea(approx)
            if len(approx) == 4 and area > area_theshold and area < full_area:
                rects.append({"cnt": approx, "area": area})

        match len(rects):
            case 0: return fake_contour
            case 1: return rects[0]["cnt"]
            case _: return max(rects, key=lambda c: c["area"])["cnt"]
