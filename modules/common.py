from math import acos, degrees
from shapely.geometry import LineString, Point


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
