import cv2
import numpy as np
import time

BLUR_CONST = 2
ADAPTIVE_THRESH_AREA = 21; ADAPTIVE_THRESH_CONST = 2
THRESHOLD_VAL = 220; THRESHOLD_MAX = 255
MIN_CONTOUR_POINTS = 100; CONTOUR_WEIGHT = 5; CONTOUR_COLOR = (0, 0, 255)
EPSILON = 0.01
HIRAR_LEGEND={"NEXT":0, "PREV":1, "FIRST":2, "PARENT":3}

def shapeDetector(thresh_image, image):
    contours, hierarchy = cv2.findContours(thresh_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    count = 0
    # image = image.copy()
    # Iterating through each contour to retrieve coordinates and hirarchy of each shape
    for i, zp in enumerate(zip(contours, hierarchy[0])):
        (contour, hirar) = zp
        if i == 0 or len(contour) < MIN_CONTOUR_POINTS or hirar[HIRAR_LEGEND["PARENT"]] < 1:
        # if i == 0 or len(contour) < MIN_CONTOUR_POINTS:
            continue

        count+=1
        
        # The 2 lines below this comment will approximate the shape we want. This can be used to get x,y locations of (approx) the shapes, for image manipulation
        # epsilon = EPSILON*cv2.arcLength(contour, True)
        # approx = cv2.approxPolyDP(contour, epsilon, True)

        # Drawing the outer-edges onto the image
        cv2.drawContours(image, contour, -1, CONTOUR_COLOR, CONTOUR_WEIGHT)
        
    print("overall shapes: ", count)
    return(image)

def frameContent(cam):
    ret,image = cam.read()

    if not ret:
        print("Error: Failed to capture image")

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) # Converting to gray image
    # edges = cv2.Canny(gray_image,200,200) ?????
    blurred_img = cv2.medianBlur(gray_image,5)

    # Setting threshold value to get new image (In simpler terms: this function checks every pixel, and depending on how
    # dark the pixel is, the threshold value will convert the pixel to either black or white (0 or 1)).
    # _, thresh_image = cv2.threshold(blurred_img, THRESHOLD_VAL, THRESHOLD_MAX, cv2.THRESH_BINARY_INV)
    thresh_image = cv2.adaptiveThreshold(blurred_img,THRESHOLD_MAX,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,51,2)

    # Retrieving outer-edge coordinates in the new threshold image
    image=shapeDetector(thresh_image,image.copy())

    # Displaying the image with the detected shapes onto the screen
    cv2.namedWindow('shapes_detected', cv2.WINDOW_NORMAL)
    cv2.imshow("shapes_detected", image)


# Image to detect shapes on below
cam = cv2.VideoCapture(0)

while(1):
    frameContent(cam)

    if cv2.waitKey(5) == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()


#TODO: limit image frame to relevant area
#TODO: internal shapes 