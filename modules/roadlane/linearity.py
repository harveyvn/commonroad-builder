from . import RoadLane
from .laneline import Laneline
from .analyzer import Analyzer
from math import floor, ceil
from shapely.geometry import Polygon, LineString, Point


class LinearLane(RoadLane):

    def process(self):
        lane_width = self.params["lane_width"]
        coords = self.params["coords"]
        image = self.params["image"]

        baseline = LineString([Point(p[0], p[1]) for p in coords])
        left_boundary = baseline.parallel_offset(distance=ceil(lane_width / 2), side="left", join_style=2)
        right_boundary = baseline.parallel_offset(distance=ceil(lane_width / 2), side="right", join_style=2)

        # Step 1: Find a region using poly points
        poly = Polygon([*list(left_boundary.coords), *list(right_boundary.coords)])

        analyzer = Analyzer(poly, image, coords, [Laneline(0, coords, lane_width / 2)])
        analyzer.run()

        return True
