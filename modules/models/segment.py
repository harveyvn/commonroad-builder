import matplotlib.pyplot as plt
from .lane import Lane, SimLane, Stripe
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
        self.simlanes: List[SimLane] = None

    def generate_simlanes(self, lines: List[Line], ratio: float, debug: bool = False):
        lanes, simlanes = [], []
        for l1, l2 in pairs(lines):
            lanes.append(Lane(left=l1, right=l2))

        for lane in lanes:
            simlanes.append(lane.get_simlane(ratio))

        if debug:
            plt.clf()
            for i, sl in enumerate(simlanes):
                sl: SimLane = sl
                left: Stripe = sl.left
                right: Stripe = sl.right
                poly = LineString([(t[0], t[1]) for t in sl.mid]).buffer(sl.width / 2, cap_style=2, join_style=2)
                patch = PolygonPatch(poly, fc='gray', ec='dimgray')
                plt.gca().add_patch(patch)
                if i == 0:
                    render_stripe(plt, left)
                elif i == len(simlanes) - 1:
                    render_stripe(plt, right)
                else:
                    render_stripe(plt, left)
                    render_stripe(plt, right)
                xs = [point[0] for point in sl.mid]
                ys = [point[1] for point in sl.mid]
                plt.plot(xs, ys, color='r')
            plt.gca().set_aspect('equal')
            plt.title("Road new CRISCE")
            plt.show()
            exit()

        self.simlanes = simlanes

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
