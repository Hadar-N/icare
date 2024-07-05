import numpy as np

def PolygonArea(dots):
    corners = [(point[0][0], point[0][1]) for point in dots]
    n = len(corners)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += corners[i][0] * corners[j][1]
        area -= corners[j][0] * corners[i][1]
    area = abs(area) / 2.0
    return area

def getRandomColor() : return int(np.random.choice(range(256)))
