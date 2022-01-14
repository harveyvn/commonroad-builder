from . import RoadLane
from .laneline import Laneline
from .analyzer import Analyzer
from math import ceil
from shapely.geometry import Polygon


class IntersectionLane(RoadLane):

    def process(self):
        lane_widths = self.params["lane_widths"]
        lengths = self.params["lengths"]
        image = self.params["image"]

        baselines = []
        for i, coord in enumerate(self.params["roads"]):
            baselines.append(Laneline(lane_id=i, coords=coord, width=lane_widths[i] / 2))

        for idx, laneline in enumerate(baselines):
            mid_line = laneline.get_linestring()
            left_boundary = mid_line.parallel_offset(distance=ceil(laneline.width), side="left", join_style=2)
            right_boundary = mid_line.parallel_offset(distance=ceil(laneline.width), side="right", join_style=2)
            poly = Polygon([*list(left_boundary.coords), *list(right_boundary.coords)])
            analyzer = Analyzer(poly, image, laneline.coords, baselines)
            analyzer.run()

        return True
