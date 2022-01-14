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

        # Define the polygon covering the road with the midline linestring, left & right boundaries
        laneline = Laneline(coords=coords, width=lane_width / 2)
        mid_line = laneline.get_linestring()
        left_boundary = mid_line.parallel_offset(distance=ceil(laneline.width), side="left", join_style=2)
        right_boundary = mid_line.parallel_offset(distance=ceil(laneline.width), side="right", join_style=2)
        poly = Polygon([*list(left_boundary.coords), *list(right_boundary.coords)])

        analyzer = Analyzer(poly, image, laneline.coords, [laneline])
        analyzer.run()

        return True
