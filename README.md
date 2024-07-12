**Oasis:**

This is a tryout for combining cv2 and pygame for animation within contours.
In it, we find contours with the camera and those act as an independent area (represented as a Sprite). the location is set by the camera and the animation is set by the area.

This project have 3 main parts:
1. setting up the stage- finding the board on which the image should focus and project and setting this perspective
2. finding relevant contours to work as the islands and filtering out the unnecessary ones
3. checking against previous contours to decide which areas are old/new, and creating/updating them accordingly.

Hoping this helps
