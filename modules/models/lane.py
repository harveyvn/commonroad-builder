from .line import Line
from .bnglane import SimLane, Stripe
from .lib import generate, flip
from modules.common import midpoint
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

    def get_simlane(self, ratio):
        ls = generate(self.left.ls, ratio, 0.1)
        rs = generate(self.right.ls, ratio, 0.1)
        ms = generate(self.mid.ls, ratio, ratio * self.width)
        return SimLane(left=Stripe(ls, self.left.num, self.left.pattern),
                       right=Stripe(rs, self.right.num, self.right.pattern),
                       mid=ms, width=ratio * self.width)

    def get_simlane_flip(self, ratio):
        ls = generate(flip(self.right.ls), ratio, 0.1)
        rs = generate(flip(self.left.ls), ratio, 0.1)
        ms = generate(flip(self.mid.ls), ratio, ratio * self.width)
        return SimLane(left=Stripe(ls, self.left.num, self.left.pattern),
                       right=Stripe(rs, self.right.num, self.right.pattern),
                       mid=ms, width=ratio * self.width)

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
