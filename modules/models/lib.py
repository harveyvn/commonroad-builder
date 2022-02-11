from shapely.geometry import LineString, Point
import numpy as np
from modules.common import translate_ls_to_new_origin


def generate(lst, r, width):
    return [(p[0] * r, p[1] * r, 0, width) for p in list(lst.coords)]


def render_stripe(ax, line):
    xs = [point[0] for point in line.points]
    ys = [point[1] for point in line.points]
    ax.plot(xs, ys, color='b',
            linewidth=4 if line.num == "double" else 1,
            linestyle=(0, (5, 10)) if line.pattern == "dashed" else "solid")


def flip(lst: LineString):
    origin = Point(lst.coords[0])
    points = np.array(list(lst.coords))
    flip = LineString(points.dot([[1, 0], [0, -1]]))
    return translate_ls_to_new_origin(flip, origin)
