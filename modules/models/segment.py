import copy
import numpy as np
import matplotlib.pyplot as plt
from .lane import Lane
from .line import Line
from .lib import render_stripe
from .bnglane import BngLane, Stripe
from typing import List
from descartes import PolygonPatch
from shapely.geometry import Polygon, LineString, Point
from modules.common import pairs, translate_ls_to_new_origin


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
        self.lanes: List[Lane] = []
        self.bnglanes: List[BngLane] = []
        self.lines: List[Line] = []

    def generate_lanes(self, lines: List[Line]):
        self.lines = lines
        lanes = []
        for l1, l2 in pairs(self.lines):
            lanes.append(Lane(left=l1, right=l2))
        self.lanes = lanes
        return self.lanes

    def get_bnglanes(self, ratio: float, debug: bool = False):
        lines = copy.deepcopy(self.lines)
        reversed_lines = copy.deepcopy(self.lines)
        lanes, bnglanes = self.lanes.copy(), []

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

            lanes = []
            for l1, l2 in pairs(lines):
                lanes.append(Lane(left=l1, right=l2))

        for lane in lanes:
            simlane = lane.get_bnglane(ratio)
            bnglanes.append(simlane)
        self.bnglanes = bnglanes

        if debug:
            plt.clf()
            fig, ax = plt.subplots(1, 1, figsize=(8, 8))
            ax = self.visualize(ax)
            ax.title.set_text("Road new CRISCE")
            plt.show()
            exit()

    def visualize(self, ax):
        for i, sl in enumerate(self.bnglanes):
            sl: BngLane = sl
            left: Stripe = sl.left
            right: Stripe = sl.right
            poly = LineString([(t[0], t[1]) for t in sl.mid]).buffer(sl.width / 2, cap_style=2, join_style=2)
            patch = PolygonPatch(poly, fc='gray', ec='dimgray')
            ax.add_patch(patch)
            if i == 0:
                render_stripe(plt, left)
            elif i == len(self.bnglanes) - 1:
                render_stripe(plt, right)
            else:
                render_stripe(plt, left)
                render_stripe(plt, right)
            xs = [point[0] for point in sl.mid]
            ys = [point[1] for point in sl.mid]
            ax.plot(xs, ys, color='r')
        ax.set_aspect('equal')
        return ax

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
