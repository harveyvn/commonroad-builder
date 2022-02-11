import matplotlib.pyplot as plt
from .lane import Lane
from .bnglane import SimLane, Stripe
from .line import Line
from .lib import render_stripe
from typing import List
from descartes import PolygonPatch
from modules.common import pairs
from shapely.geometry import Polygon, LineString


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
        self.simlanes: List[SimLane] = []

    def generate_lanes(self, lines: List[Line]):
        lanes = []
        for l1, l2 in pairs(lines):
            lanes.append(Lane(left=l1, right=l2))
        self.lanes = lanes
        return self.lanes

    def generate_simlanes(self, ratio: float, debug: bool = False):
        simlanes = []
        for lane in self.lanes:
            simlane = lane.get_simlane(ratio) if self.angle == -90 else lane.get_simlane(ratio)
            simlanes.append(simlane)

        if debug:
            plt.clf()
            fig, ax = plt.subplots(1, 1, figsize=(8, 8))
            ax = self.visualize(ax)
            ax.title.set_text("Road new CRISCE")
            plt.show()
            exit()

        self.simlanes = simlanes

    def visualize(self, ax):
        for i, sl in enumerate(self.simlanes):
            sl: SimLane = sl
            left: Stripe = sl.left
            right: Stripe = sl.right
            poly = LineString([(t[0], t[1]) for t in sl.mid]).buffer(sl.width / 2, cap_style=2, join_style=2)
            patch = PolygonPatch(poly, fc='gray', ec='dimgray')
            ax.add_patch(patch)
            if i == 0:
                render_stripe(plt, left)
            elif i == len(self.simlanes) - 1:
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
