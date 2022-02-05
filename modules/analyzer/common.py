from modules.common import translate_ls_to_new_origin
from shapely.geometry import Point, LineString
from typing import List


def create(img, point_x: int, ls: LineString, num_points: int = 15):
    """
    Generate the sliding window line.

    Args:
        point_x (int): x point to generate window line.
        img (np.array): an image to find the color value of a particular position.
        ls (LineString): a based linestring that use to generate a window line.
        num_points (int): a number of point we extract from the base linestring.
    """
    window_line = translate_ls_to_new_origin(ls, Point(point_x, 0))
    if list(window_line.coords)[-1][1] < 0:
        window_line = translate_ls_to_new_origin(ls, Point(point_x, img.shape[0]))
    # Remove points not in an image
    coords, checked_coords = list(window_line.coords), []
    for p in coords:
        try:
            if int(img[int(p[1]), int(p[0])]) > -1:
                checked_coords.append(p)
        except IndexError:
            pass

    # Take first num_points from a line string
    if len(checked_coords) < 3:
        return LineString(coords)
    return LineString(checked_coords[0:num_points])


def find(points: List, img):
    """
    Find the first non-zero point which actually reveals the color value.

    Args:
        points (List): list of points extracting from linestring.
        img (np.array): an image to find the color value of a particular position.
    """
    starting_color_index = 0
    for i, p in enumerate(points):
        val_point = int(img[p[1], p[0]])
        # print(i, val_point)
        if starting_color_index == 0 and val_point > 0:
            starting_color_index = i

    # print("Starting index is ", starting_color_index)
    return starting_color_index


def analyze(points: List, img):
    """
    Extract number of points, number of non-zero points and zero points.

    Args:
        points (List): list of points extracting from linestring.
        img (np.array): an image to find the color value of a particular position.
    """
    zeros, non_zeros = 0, 0
    length = len(points)
    for i, p in enumerate(points):
        try:
            val = int(img[p[1], p[0]])
        except IndexError:
            val = 0
        # print(i, val)
        if val > 0:
            non_zeros += 1
        else:
            zeros += 1

    return length, non_zeros, zeros
