from enum import Enum
import math
from typing import List, Tuple
"""A rectangle here is a 4-tuple (or list) of the left, bottom, right and top x/y values respectively.
A point is a 2-tuple (or list) of the x/y coordinates. A polygon is a list of points."""

GRID_SQUARE_WIDTH = 100000
Polygons = List[List[Tuple[float, float]]]


# Coordinates are bottom left corner of each grid square
class OrdnanceSurveyGridSquare(Enum):
    SV = (0, 0)
    SW = (100000, 0)
    SX = (200000, 0)
    SY = (300000, 0)
    SZ = (400000, 0)
    TV = (500000, 0)
    SR = (100000, 100000)
    SS = (200000, 100000)
    ST = (300000, 100000)
    SU = (400000, 100000)
    TQ = (500000, 100000)
    TR = (600000, 100000)
    SM = (100000, 200000)
    SN = (200000, 200000)
    SO = (300000, 200000)
    SP = (400000, 200000)
    TL = (500000, 200000)
    TM = (600000, 200000)
    SH = (200000, 300000)
    SJ = (300000, 300000)
    SK = (400000, 300000)
    TF = (500000, 300000)
    TG = (600000, 300000)
    SC = (200000, 400000)
    SD = (300000, 400000)
    SE = (400000, 400000)
    TA = (500000, 400000)
    NW = (100000, 500000)
    NX = (200000, 500000)
    NY = (300000, 500000)
    NZ = (400000, 500000)
    OV = (500000, 500000)
    NR = (100000, 600000)
    NS = (200000, 600000)
    NT = (300000, 600000)
    NU = (400000, 600000)
    NL = (0, 700000)
    NM = (100000, 700000)
    NN = (200000, 700000)
    NO = (300000, 700000)
    NP = (400000, 700000)
    NF = (0, 800000)
    NG = (100000, 800000)
    NH = (200000, 800000)
    NJ = (300000, 800000)
    NK = (400000, 800000)
    NA = (0, 900000)
    NB = (100000, 900000)
    NC = (200000, 900000)
    ND = (300000, 900000)
    NE = (400000, 900000)
    HW = (100000, 1000000)
    HX = (200000, 1000000)
    HY = (300000, 1000000)
    HZ = (400000, 1000000)
    HT = (300000, 1100000)
    HU = (400000, 1100000)
    HO = (300000, 1200000)
    HP = (400000, 1200000)


def grid_square_for_point(point):
    bottom_left_x = (math.floor(point[0] / GRID_SQUARE_WIDTH) * GRID_SQUARE_WIDTH)
    bottom_left_y = (math.floor(point[1] / GRID_SQUARE_WIDTH) * GRID_SQUARE_WIDTH)
    for square in OrdnanceSurveyGridSquare:
        if bottom_left_x == square.value[0] and bottom_left_y == square.value[1]:
            return square


def _multiples_of_n_between_p_and_q(n, p, q):
    multiples = []
    min_pq, max_pq = min(p, q), max(p, q)
    smallest_possible_n_count = math.ceil(min_pq / n)
    n_count = smallest_possible_n_count
    while n_count * n <= max_pq:
        multiples.append(n_count * n)
        n_count += 1
    return multiples


def grid_squares_intersecting_line(point_a, point_b):
    """Given points a and b, return a list of grid squares
    which the line joining the points intersects with."""
    intersected_squares = set([])
    ax, ay, bx, by = point_a[0], point_a[1], point_b[0], point_b[1]
    delta_x, delta_y = bx - ax, by - ay
    gradient = delta_y / delta_x if delta_x != 0 else None  # Use None for infinite gradient
    square_a, square_b = grid_square_for_point(point_a), grid_square_for_point(point_b)
    intersected_squares.add(square_a) if square_a is not None else None
    intersected_squares.add(square_b) if square_b is not None else None
    if gradient is not None:
        for multiple in _multiples_of_n_between_p_and_q(GRID_SQUARE_WIDTH, ax, bx):
            vertical_grid_line_intersection = (multiple, (multiple - ax) * gradient + ay)
            square = grid_square_for_point(vertical_grid_line_intersection)
            intersected_squares.add(square) if square is not None else None
    if gradient != 0:
        inverse_gradient = 1 / gradient if gradient is not None else 0
        for multiple in _multiples_of_n_between_p_and_q(GRID_SQUARE_WIDTH, ay, by):
            horizontal_grid_line_intersection = ((multiple - ay) * inverse_gradient + ax, multiple)
            square = grid_square_for_point(horizontal_grid_line_intersection)
            intersected_squares.add(square) if square is not None else None
    return intersected_squares


def extract_polygons(geoJson: dict) -> Polygons:
    polygons: Polygons = []
    if geoJson["type"] == "FeatureCollection":
        for feature in geoJson["features"]:
            geometry = feature["geometry"]
            for coordinates in geometry["coordinates"]:
                process_coordinates(coordinates, polygons)
    elif geoJson["type"] == "Feature":
        geometry = geoJson["geometry"]
        for coordinates in geometry["coordinates"]:
            process_coordinates(coordinates, polygons)
    return polygons


def process_coordinates(coordinates, polygons):
    if type(coordinates[0][0]) == float:
        polygons.append(coordinates)
    else:
        for j in range(len(coordinates)):
            process_coordinates(coordinates[j], polygons)

def extent_rectangle_for_polygons(polygons: Polygons) -> Tuple[float, float, float, float]:
    """
    Expecting array of polygons
    :param polygons:
    :return: min_x,min_y,max_x,max_y
    """
    min_x, min_y = 9999999999, 9999999999
    max_x, max_y = -9999999999, -9999999999
    for polygon in polygons:
        for vertex in polygon:
            min_x = min(min_x, vertex[0])
            max_x = max(max_x, vertex[0])
            min_y = min(min_y, vertex[1])
            max_y = max(max_y, vertex[1])
    return min_x, min_y, max_x, max_y


def grid_squares_for_rectangle(rectangle):
    """Returns a list of OS grid squares intersecting the rectangle"""
    left, bottom, right, top = rectangle[0], rectangle[1], rectangle[2], rectangle[3]
    grid_squares = set([])
    y = bottom
    while y <= top:
        x = left
        while x < right:
            square = grid_square_for_point((x, y))
            grid_squares.add(square.name) if square is not None else None
            x += GRID_SQUARE_WIDTH
        square = grid_square_for_point((right, y))
        grid_squares.add(square.name) if square is not None else None
        y += GRID_SQUARE_WIDTH
    x = left
    while x < right:
        square = grid_square_for_point((x, top))
        grid_squares.add(square.name) if square is not None else None
        x += GRID_SQUARE_WIDTH
    square = grid_square_for_point((right, top))
    grid_squares.add(square.name) if square is not None else None
    
    return grid_squares


def rectangle_intersection_for_grid_square(rectangle, square):
    """For a given rectangle (min_x, min_y, max_x, max_y), returns a rectangle
    forming the intersection of the original rectangle with the given OS grid square, or None if
    they do not intersect."""
    left = max(rectangle[0], square.value[0])
    bottom = max(rectangle[1], square.value[1])
    right = min(rectangle[2], square.value[0] + GRID_SQUARE_WIDTH)
    top = min(rectangle[3], square.value[1] + GRID_SQUARE_WIDTH)
    if right < square.value[0] or left >= square.value[0] + GRID_SQUARE_WIDTH \
            or top < square.value[1] or bottom >= square.value[1] + GRID_SQUARE_WIDTH:
        return None
    else:
        return left, bottom, right, top
