from .line import Line
from .bnglane import BngLane, Stripe
from .lib import generate
from modules.common import midpoint, smooth_line
from shapely.geometry import LineString, Point


class Lane:
    def __init__(self, left: Line, right: Line):
        self.left = left
        self.right = right

        mps = []
        for l, r in zip(list(left.ls.coords), list(right.ls.coords)):
            point_left = Point(l[0], l[1])
            point_right = Point(r[0], r[1])
            mps.append(midpoint(point_left, point_right))
            self.width = point_left.distance(point_right)
        self.mid = Line(ls=LineString(mps))

    def get_bnglane(self, ratio, angle):
        ls = generate(self.left.ls, ratio, 0.1)
        rs = generate(self.right.ls, ratio, 0.1)
        ms = generate(self.mid.ls, ratio, ratio * self.width)
        # Smooth line not applied to vertical roads
        if (-5 < angle < 5) is False:
            ls = smooth_line(ls)
            rs = smooth_line(rs)
            ms = smooth_line(ms)
        return BngLane(left=Stripe(ls, self.left.num, self.left.pattern),
                       right=Stripe(rs, self.right.num, self.right.pattern),
                       mid=ms, width=ratio * self.width)

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
