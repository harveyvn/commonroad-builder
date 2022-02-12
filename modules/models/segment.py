import copy
import numpy as np
import matplotlib.pyplot as plt
from .lane import Lane
from .line import Line
from .bng_segment import BngSegement
from typing import List
from shapely.geometry import Polygon, LineString, Point
from modules.common import pairs, translate_ls_to_new_origin, midpoint


class Segment:
    def __init__(self, kind, mid_line: LineString, width: float = 0, road_id: int = 0, reversed: bool = False,
                 left_boundary: LineString = None, right_boundary: LineString = None):
        self.id = road_id
        self.kind = kind
        self.left_boundary = left_boundary
        self.right_boundary = right_boundary
        self.mid_line = mid_line
        self.width = width
        self.poly = Polygon([*list(left_boundary.coords), *list(right_boundary.coords)])
        self.reversed = reversed
        self.lanes: [Lane] = []
        self.angle: float = 0
        self.is_horizontal = False
        self.is_vertical = False

    def get_bng_segment(self, lines: List[Line], ratio: float, debug: bool = False):
        lines = copy.deepcopy(lines)
        reversed_lines = copy.deepcopy(lines)

        if self.angle == -90:
            for i, line in enumerate(lines):
                target = lines[i]
                points = np.array(list(target.ls.coords))
                flip = LineString(points.dot([[1, 0], [0, -1]]))
                first = Point(list(lines[i].ls.coords)[0])
                last = Point(list(lines[len(lines) - 1 - i].ls.coords)[0])
                move = translate_ls_to_new_origin(flip, Point(first.x, last.y))
                reversed_lines[i].ls = move
            lines = reversed_lines

        first, last = lines[0], lines[-1]
        left = copy.deepcopy(first)
        right = copy.deepcopy(last)

        mps, width = [], 0
        for l, r in zip(list(left.ls.coords), list(right.ls.coords)):
            point_left = Point(l[0], l[1])
            point_right = Point(r[0], r[1])
            mps.append(midpoint(point_left, point_right))
            if point_right.distance(point_left) > width:
                width = point_right.distance(point_left)
        center = Line(ls=LineString(mps))

        marks = []
        if len(lines) > 2:
            for i, l in enumerate(lines):
                if (i == 0 or i == (len(lines) - 1)) is False:
                    marks.append(l)

        bs = BngSegement(left, right, center, marks, width, ratio, self.angle)

        if debug:
            plt.clf()
            fig, ax = plt.subplots(1, 1, figsize=(8, 8))
            ax = bs.visualize(ax)
            ax.title.set_text("New Road with Lanelines")
            plt.show()
            exit()

        return bs

    def generate_lanes(self, lines: List[Line]):
        lanes = []
        for l1, l2 in pairs(lines):
            lanes.append(Lane(left=l1, right=l2))
        self.lanes = lanes
        return self.lanes

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
