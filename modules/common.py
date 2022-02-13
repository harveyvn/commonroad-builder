from math import acos, degrees
from shapely.geometry import LineString, Point
import shapely.wkt
import shapely.ops
import numpy.polynomial.polynomial as poly
import numpy as np
from typing import List
import matplotlib.pyplot as plt


def reverse_geom(geom):
    def _reverse(x, y, z=None):
        if z:
            return x[::-1], y[::-1], z[::-1]
        return x[::-1], y[::-1]

    return shapely.ops.transform(_reverse, geom)


def pairs(lst):
    for i in range(1, len(lst)):
        yield lst[i - 1], lst[i]


def translate_ls_to_new_origin(lst: LineString, new_origin: Point):
    """
    Translate an existed linestring to a new origin.

    Args:
        lst (LineString): An existed linestring
        new_origin (Point): A new origin of a new linestring eg (x, y)
    Returns:
        new_lst (LineString)
    """
    import math
    first, last = lst.boundary
    dx = first.x - new_origin.x
    dy = first.y - new_origin.y

    new_lst = list()
    for p in list(lst.coords):
        new_lst.append((p[0] - dx, p[1] - dy))

    if math.isclose(lst.length, LineString(new_lst).length, rel_tol=1e-3) is False:
        # two values are approximately equal or “close” to each other, 3 digits after comma
        print(f'Exception: Generated new line is not the same length! lst: '
              f'{lst.length} vs new_lst {LineString(new_lst).length}')
    return LineString(new_lst)


def slice_when(predicate, iterable):
    i, x, size = 0, 0, len(iterable)
    while i < size - 1:
        if predicate(iterable[i], iterable[i + 1]):
            yield iterable[x:i + 1]
            x = i + 1
        i += 1
    yield iterable[x:size]


def dot(vA, vB):
    """
    Return the dot product between 2 vectors
    """
    return vA[0] * vB[0] + vA[1] * vB[1]


def angle(lineA, lineB):
    """
    Return the angle between 2 linestrings
    """

    # Get nicer vector form
    vA = [(lineA[0][0] - lineA[1][0]), (lineA[0][1] - lineA[1][1])]
    vB = [(lineB[0][0] - lineB[1][0]), (lineB[0][1] - lineB[1][1])]
    # Get dot prod
    dot_prod = dot(vA, vB)
    # Get magnitudes
    magA = dot(vA, vA) ** 0.5
    magB = dot(vB, vB) ** 0.5
    # Get cosine value
    cos_ = dot_prod / magA / magB
    # Get angle in radians and then convert to degrees
    angle = acos(dot_prod / magB / magA)
    # Basically doing angle <- angle mod 360
    ang_deg = degrees(angle) % 360

    if ang_deg - 180 >= 0:
        return 360 - ang_deg

    return ang_deg


def midpoint(p1: Point, p2: Point):
    return Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)


def order_points(points, ind: int = 0):
    is_horizontal, is_vertical = orient(points)
    points_new = [points.pop(ind)]  # initialize a new list of points with the known first point
    pcurr = points_new[-1]  # initialize the current point (as the known point)
    while len(points) > 0:
        d = np.linalg.norm(np.array(points) - np.array(pcurr),
                           axis=1)  # distances between pcurr and all other remaining points
        ind = d.argmin()  # index of the closest point
        points_new.append(points.pop(ind))  # append the closest point to points_new
        pcurr = points_new[-1]  # update the current point

    if is_horizontal:
        points_new.sort(key=lambda x: x[0], reverse=True)
    if is_vertical:
        points_new.sort(key=lambda x: x[1])
    return points_new


def orient(line):
    lineA, lineB = line, [[0, 0], [1, 0]]
    diff = angle(lineA, lineB)
    is_horizontal = True if -2 <= diff <= 6 else False
    if is_horizontal is False:
        is_horizontal = True if 175 <= diff <= 183 else False
    is_vertical = True if 80 <= diff <= 100 else False
    return is_horizontal, is_vertical


def find_boundaries(image, line):
    is_horizontal, is_vertical = orient(line)
    lineA, lineB = line, [[0, 0], [1, 0]]
    a, b = Point(lineA[0]), Point(lineA[1])
    lefts, rights = [[], []], [[], []]

    xmax_img, ymax_img = image.shape[1], image.shape[0]
    if is_horizontal:  # // (0, 0), (1, 0)
        lefts = [[a.x, 0], [b.x, 0]]
        rights = [[b.x, ymax_img], [a.x, ymax_img]]
        if a.x > b.x:  # // (1, 0), (0, 0)
            lefts.reverse()
            rights.reverse()

    if is_vertical:  # // (0, 0), (0, 1)
        lefts = [[xmax_img, a.y], [xmax_img, b.y]]
        rights = [[0, b.y], [0, a.y]]
        if a.y > b.y:  # // (0, 1), (0, 0)
            lefts.reverse()
            rights.reverse()

    return lefts, rights


def interpolate(coords: List, axis_idx: int, image: np.array):
    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]

    if axis_idx == 1:
        coefs = poly.polyfit(xs, ys, 2)
        margin_right = 20

        poly_xs = [x for x in range(int(xs[0]), int(image.shape[1] - margin_right))]
        poly_ys = poly.polyval(poly_xs, coefs)
        coords = [(x, y) for x, y in zip(poly_xs, poly_ys)]
    # import matplotlib.pyplot as plt
    #
    # plt.imshow(image, cmap='gray')
    # plt.plot(xs, ys, '.')
    # # plt.plot(poly_xs, poly_ys, '.')
    # plt.show()
    #
    # print(coords)
    if axis_idx == 0:
        print("From Parallel interpolate")
        exit()
    return coords


def smooth_line(coords: List, debug: bool = False):
    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]
    coefs = poly.polyfit(xs, ys, 2)

    first, last = xs[0], xs[-1]
    poly_xs = np.arange(start=first, stop=last, step=abs(last - first) / 400).tolist()
    poly_ys = poly.polyval(poly_xs, coefs)
    coords = [(x, y) for x, y in zip(poly_xs, poly_ys)]

    if debug:
        fig, ax = plt.subplots(1, 2, figsize=(12, 4))
        ax[0].plot(xs, ys, '.', label="Origin")
        ax[0].plot(poly_xs, poly_ys, '-', label="Interpolate")
        ax[0].set_aspect("auto")
        ax[0].legend(loc='lower right')
        ax[1].plot(xs, ys, '.', label="Origin")
        ax[1].plot(poly_xs, poly_ys, '-', label="Interpolate")
        ax[1].set_aspect("equal")
        plt.show()
        exit()

    return coords
