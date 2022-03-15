from typing import List

from descartes import PolygonPatch
from shapely.geometry import LineString

from .line import Line
from .stripe import Stripe
from .lib import generate, render_stripe


class BngSegement:
    def __init__(self, left: Line, right: Line, center: Line, marks: List[Line],
                 width: float, ratio: float, angle: float):
        is_sml = True if (-5 < angle < 5) is False else False

        self.left = Stripe(generate(left.ls, ratio, 0.1, is_sml), left.num, left.pattern)
        self.right = Stripe(generate(right.ls, ratio, 0.1, is_sml), right.num, right.pattern)
        self.center = Stripe(generate(center.ls, ratio, ratio * width, is_sml))
        self.marks = [Stripe(generate(m.ls, ratio, 0.1, is_sml), m.num, m.pattern) for m in marks]
        self.width = ratio * width

    def visualize(self, ax, show_center: bool = True):
        poly = LineString([(t[0], t[1]) for t in self.center.points]).buffer(self.width / 2, cap_style=2, join_style=2)
        patch = PolygonPatch(poly, fc='gray', ec='gray')
        ax.add_patch(patch)
        if show_center:
            xs = [point[0] for point in self.center.points]
            ys = [point[1] for point in self.center.points]
            ax.plot(xs, ys, color='coral')
        render_stripe(ax, self.left, "blue")
        render_stripe(ax, self.right, "blue")
        for m in self.marks:
            render_stripe(ax, m, "yellow")
        return ax

    def get_lines(self):
        return {
            "l": self.left.points,
            "r": self.right.points,
            "c": self.center.points,
            "m": [m.points for m in self.marks]
        }

    def set_lines(self, lines: dict):
        self.left.points = lines['l']
        self.right.points = lines['r']
        self.center.points = lines['c']
        for i, m in enumerate(self.marks):
            self.marks[i].points = lines['m'][i]

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
