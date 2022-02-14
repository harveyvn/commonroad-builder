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
        self.bng_segment = None
        self.lines: [Line] = []

    def flip(self, height: float, debug: bool = False):
        assert len(self.lines) > 0
        lines = copy.deepcopy(self.lines)
        flipped_lines = copy.deepcopy(lines)

        for i, line in enumerate(lines):
            target = lines[i]
            ps = [(p[0], height - p[1]) for p in list(target.ls.coords)]
            flip = LineString(ps)
            flipped_lines[i].ls = flip

        if debug:
            plt.clf()
            fig, ax = plt.subplots(1, 1, figsize=(8, 8))
            self.visualize(ax, flipped_lines, "Segment with original Lane Lines")
            exit()

        return flipped_lines

    def get_bng_segment(self, lines: List[Line], ratio: float, debug: bool = False):
        lines = copy.deepcopy(lines)
        first, last = lines[0], lines[-1]
        left = copy.deepcopy(first)
        right = copy.deepcopy(last)
        assert len(list(left.ls.coords)) == len(list(right.ls.coords))

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

        self.bng_segment = bs

    def generate_lanes(self, lines: List[Line]):
        lanes = []
        for l1, l2 in pairs(lines):
            lanes.append(Lane(left=l1, right=l2))
        self.lanes = lanes
        return self.lanes

    @staticmethod
    def visualize(ax, lines, title: str = "Segment with original Lane Lines"):
        for line in lines:
            xs = [p[0] for p in list(line.ls.coords)]
            ys = [p[1] for p in list(line.ls.coords)]
            ax.plot(xs, ys,
                    linewidth=3 if line.num == "double" else 1,
                    linestyle=(0, (5, 2)) if line.pattern == "dashed" else "solid")
        ax.title.set_text(title)
        return ax

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
