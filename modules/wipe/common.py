from math import hypot
from typing import List
from shapely.geometry import Polygon, LineString, Point, MultiLineString
import matplotlib.pyplot as plt


def get_poly(lines):
    l = LineString([[p[0], p[1]] for p in lines['l']])
    r = LineString([[p[0], p[1]] for p in lines['r']])
    return Polygon([*list(l.coords), *list(r.coords)[::-1]])


def where_it_is(line: LineString, point: Point):
    first, last = line.boundary
    aX, aY = first.x, first.y
    bX, bY = last.x, last.y
    cX, cY = point.x, point.y

    val = ((bX - aX) * (cY - aY) - (bY - aY) * (cX - aX))
    thresh = 1e-9
    if val >= thresh:
        return 0  # left
    elif val <= -thresh:
        return 1  # right
    else:
        return -1


def transform(lines: List, poly: Polygon):
    for i, line in enumerate(lines):
        ls_temp = LineString([[p[0], p[1]] for p in line])
        lines[i] = ls_temp
        if lines[i].intersects(poly):
            merged = lines[i].intersection(poly)
            lines[i] = lines[i].difference(merged)

            if type(lines[i]) == MultiLineString:
                longest_lst = None
                max_points = 0
                for lst in lines[i]:
                    if len(list(lst.coords)) > max_points:
                        max_points = len(list(lst.coords))
                        longest_lst = lst
                lines[i] = longest_lst

            assert type(lines[i]) == LineString
        try:
            lines[i] = list(lines[i].coords)
        except Exception as ex:
            fig, ax = plt.subplots()
            xs = [p[0] for p in lines[i].geoms[0].coords]
            ys = [p[1] for p in lines[i].geoms[0].coords]
            ax.plot(xs, ys, linewidth=1, linestyle="solid", color="red")
            plt.show()
            print(lines[i])
            exit()
    return lines


def collapse(sm: dict, poly: Polygon):
    sm['l'] = transform([sm['l']], poly)[0]
    sm['r'] = transform([sm['r']], poly)[0]
    sm['m'] = transform(sm['m'], poly)
    return sm


def length(ls):
    return sum(hypot(x1 - x2, y1 - y2) for (x1, y1), (x2, y2) in zip(ls, ls[1:]))
