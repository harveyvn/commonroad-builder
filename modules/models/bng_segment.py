from typing import List

from descartes import PolygonPatch
from shapely.geometry import LineString, Point

from .line import Line
from .stripe import Stripe
from .lib import generate, render_stripe
from modules.common import translate_ls_to_new_origin


class BngSegement:
    def __init__(self, left: Line, right: Line, center: Line, marks: List[Line],
                 width: float, ratio: float, angle: float):
        is_sml = True if (-5 < angle < 5) is False else False

        self.left = Stripe(generate(left.ls, ratio, 0.1, is_sml), left.num, left.pattern)
        self.right = Stripe(generate(right.ls, ratio, 0.1, is_sml), right.num, right.pattern)
        self.center = Stripe(generate(center.ls, ratio, ratio * width, is_sml))
        self.marks = [Stripe(generate(m.ls, ratio, 0.1, is_sml), m.num, m.pattern) for m in marks]
        self.width = ratio * width

    def transform(self, dx: float, dy: float):
        def run(stripe: Stripe):
            ls = LineString([(p[0], p[1]) for p in stripe.points])
            width = stripe.points[0][2]
            p1 = Point([(p[0], p[1]) for p in stripe.points][0])
            origin = Point(p1.x - dx, p1.y - dy)
            ls = translate_ls_to_new_origin(ls, origin)
            return generate(ls, 1, width, False)

        self.left.points = run(self.left)
        self.right.points = run(self.right)
        self.center.points = run(self.center)
        for m in self.marks:
            m.points = run(m)

    def visualize(self, ax):
        poly = LineString([(t[0], t[1]) for t in self.center.points]).buffer(self.width / 2, cap_style=2, join_style=2)
        patch = PolygonPatch(poly, fc='gray', ec='dimgray')
        ax.add_patch(patch)
        xs = [point[0] for point in self.center.points]
        ys = [point[1] for point in self.center.points]
        ax.plot(xs, ys, color='coral')
        render_stripe(ax, self.left, "blue")
        render_stripe(ax, self.right, "blue")
        for m in self.marks:
            render_stripe(ax, m, "yellow")
        return ax
