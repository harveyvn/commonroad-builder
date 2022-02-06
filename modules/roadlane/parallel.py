from .creator import RoadLane
from .laneline import Laneline
from shapely.geometry import LineString
from modules.constant import CONST
from modules.models import Segment
from modules.common import find_left_right_boundaries, order_points


import numpy.polynomial.polynomial as poly


class ParallelLane(RoadLane):
    def process(self):
        coords = order_points(self.params["roads"][0])
        image = self.params["image"]
        xs = [p[0] for p in coords]
        ys = [p[1] for p in coords]
        coefs = poly.polyfit(xs, ys, 2)
        poly_xs = [x for x in range(int(xs[0]), int(image.shape[1]))]
        poly_ys = poly.polyval(poly_xs, coefs)
        coords = [(x, y) for x, y in zip(poly_xs, poly_ys)]
        # import matplotlib.pyplot as plt
        # plt.imshow(image, cmap='gray')
        # plt.plot(poly_xs, poly_ys, '.')
        # plt.show()

        baseline = Laneline(lane_id=0, coords=coords, width=0)
        lefts, rights, diff = find_left_right_boundaries(self.params["image"], baseline.get_line())

        segment = Segment(road_id=baseline.id,
                          left_boundary=LineString(lefts),
                          right_boundary=LineString(rights),
                          mid_line=baseline.get_linestring(),
                          kind=CONST.ROAD_PARALLEL)

        segment.is_horizontal = True if -2 <= diff <= 2 else False
        segment.is_vertical = True if 88 <= diff <= 92 else False

        return self.params["image"], [baseline], [segment]
