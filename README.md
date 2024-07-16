## Oasis:

This is a tryout project for combining cv2 and pygame for animation within shapes detected by camera, as inspired by the [Oasis Tangible Interface](https://www.youtube.com/watch?v=XNpFXMlqceM "Youtube presentation of original version") presented in SIGGRAPH 2008.

This project has 2 versions for main files, while using the same consts, sprites and helper functions:

***

#### Helper Files:

* **setup_helpers.py**
The first thing in both main files is to initialize the board: find the contour of physical board in the image, check its' resolution vs the projected resolution and return a matrix to control the perspective of all images after.
**important functions**: screenSetup- deciding on the window size; getTransformationMatrix- finds the board, calculates the projected area from it and returns the matrix.
**notice**: for successful initialization, the board should start off "clean".

* **internals_management_helpers.py**
including the functions for controlling the InternalSprites, detecting collisions, how many sprites to create, in what location, etc.
**notice**: some functions in ContourPolygon has their own versions to it and not always use helper functions.

---

#### Main Files:

* **alltogether.py**
This version is based off detecting contours, then using said contours as sprites and each creates their own internal sprites. It compares old and new contours (as sprites) to decide which are new.
_This structure proved to have many issues, for example detection of dark areas locked within other areas vs clear areas locked within contours, extreme sensitivity to noise and inability to merge or split contours while keeping the internal sprites._ While many of these issues are solvable, the solution chosen is to go with another structure, as detailed in the other main file.
This file is kept as reference for people trying to use contours as sprites.

* **alltogether_as_mask.py**
This version uses the initial image for comparison with current image to detect newly darkened areas. The internal sprites are held by the main file, all are calculated and used in the same group. Instead of checking contours against previous versions, we just check overlapping area between internal shapes and the calculated mask.

---

#### Sprites:

* **ContourPolygon.py**
used in _alltogether.py_ only, draws the physical polygon, holds InternalSprites and updates both it's own shape and the InternalSprite's movement

* **InternalSprite.py**
represent an "internal" (sometime referred to as fish). moves on its' own based on a randomized direction and speed. the collisions are checked from above.

***

Hope it helps :)
